#!/usr/bin/env python3
"""
Hook PostToolUse para Write/Edit: vigilante ortográfico.

Intercepta las operaciones de escritura y edición para detectar palabras
en castellano que se escriben frecuentemente sin tilde. Cuando encuentra
errores, informa por stderr con la voz de "El Rompe-cosas" (QA).

No bloquea la operación (exit 0 siempre), solo avisa. La idea es que
las faltas de ortografía se corrijan inmediatamente, antes de que se
acumulen y cueste más arreglarlas.

Solo inspecciona ficheros de texto que probablemente contengan castellano:
documentación, código fuente (comentarios/strings), plantillas y HTML.
Ignora ficheros binarios, JSON puro, lockfiles y node_modules.
"""

import json
import os
import re
import sys


# --- Extensiones de fichero a inspeccionar ---

# Solo revisamos ficheros donde es probable encontrar texto en castellano.
# Los .json, .lock, .yaml de configuración se excluyen porque sus valores
# suelen ser identificadores técnicos, no prosa.
TEXT_EXTENSIONS = {
    ".md", ".txt", ".html", ".htm",
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".vue", ".svelte", ".astro",
    ".sh", ".bash", ".zsh",
    ".css", ".scss",
    ".xml", ".svg",
    ".rst", ".adoc",
    ".toml",  # solo pyproject.toml con descripciones
}

# --- Directorios y ficheros a ignorar ---

IGNORE_PATHS = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    ".next", ".nuxt", ".venv", "venv", "env",
}

# --- Diccionario de palabras sin tilde -> con tilde ---

# Cada entrada mapea la forma incorrecta (sin tilde) a la correcta.
# Se buscan como palabras completas (\b) para evitar falsos positivos.
# El diccionario se organiza por terminación para facilitar el mantenimiento.
#
# Criterio de inclusión: solo palabras que aparecen con frecuencia en
# documentación técnica y código. No se incluyen palabras del lenguaje
# coloquial que rara vez aparecen en un proyecto de software.
ACCENT_WORDS = {
    # -ción
    "funcion": "función",
    "configuracion": "configuración",
    "informacion": "información",
    "autenticacion": "autenticación",
    "descripcion": "descripción",
    "documentacion": "documentación",
    "sesion": "sesión",
    "version": "versión",
    "conexion": "conexión",
    "aplicacion": "aplicación",
    "operacion": "operación",
    "validacion": "validación",
    "creacion": "creación",
    "instalacion": "instalación",
    "actualizacion": "actualización",
    "ejecucion": "ejecución",
    "implementacion": "implementación",
    "investigacion": "investigación",
    "migracion": "migración",
    "navegacion": "navegación",
    "notificacion": "notificación",
    "optimizacion": "optimización",
    "configuracion": "configuración",
    "compilacion": "compilación",
    "integracion": "integración",
    "autorizacion": "autorización",
    "verificacion": "verificación",
    "especificacion": "especificación",
    "resolucion": "resolución",
    "asociacion": "asociación",
    "generacion": "generación",
    # -ía
    "auditoria": "auditoría",
    "categoria": "categoría",
    "estrategia": "estrategia",  # sin tilde, correcta así
    "tecnologia": "tecnología",
    "metodologia": "metodología",
    "dependencia": "dependencia",  # sin tilde, correcta así
    # -ico/-ica
    "automatico": "automático",
    "codigo": "código",
    "metodo": "método",
    "numero": "número",
    "parametro": "parámetro",
    "unico": "único",
    "publico": "público",
    "tecnico": "técnico",
    "basico": "básico",
    "dinamico": "dinámico",
    "estatico": "estático",
    "especifico": "específico",
    "generico": "genérico",
    "semantico": "semántico",
    "sintactico": "sintáctico",
    "critico": "crítico",
    "logico": "lógico",
    "grafico": "gráfico",
    # -ás, -én, -és, -ón
    "tambien": "también",
    "pagina": "página",
    "modulo": "módulo",
    "ultimo": "último",
    "minimo": "mínimo",
    "maximo": "máximo",
    "valido": "válido",
    "invalido": "inválido",
    "rapido": "rápido",
    "explicito": "explícito",
    "implicito": "implícito",
    "indice": "índice",
    "analisis": "análisis",
    "diagnostico": "diagnóstico",
    "proposito": "propósito",
    "vehiculo": "vehículo",
    "credito": "crédito",
    "debito": "débito",
    "calculo": "cálculo",
    "catalogo": "catálogo",
    "simbolo": "símbolo",
    "titulo": "título",
    "arbol": "árbol",
    "caracter": "carácter",
}

# Eliminar entradas donde la forma "incorrecta" es en realidad correcta
# (palabras que no llevan tilde). Esto evita falsos positivos.
ACCENT_WORDS = {k: v for k, v in ACCENT_WORDS.items() if k != v}

# Compilar un único patrón regex con todas las palabras para eficiencia.
# Se usa re.IGNORECASE para capturar "Funcion", "FUNCION", "funcion".
_WORDS_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in ACCENT_WORDS) + r")\b",
    re.IGNORECASE,
)

# Umbral mínimo de faltas para emitir aviso (evita ruido por una sola errata)
MIN_FINDINGS = 1


def should_inspect(file_path: str) -> bool:
    """Determina si un fichero merece inspección ortográfica.

    Se excluyen ficheros binarios, lockfiles, directorios de dependencias
    y extensiones que no suelen contener prosa en castellano.

    Args:
        file_path: Ruta absoluta o relativa del fichero.

    Returns:
        True si el fichero debería inspeccionarse.
    """
    if not file_path:
        return False

    # Ignorar rutas dentro de directorios excluidos
    parts = file_path.replace("\\", "/").split("/")
    if any(part in IGNORE_PATHS for part in parts):
        return False

    # Solo inspeccionar extensiones de texto conocidas
    _, ext = os.path.splitext(file_path)
    return ext.lower() in TEXT_EXTENSIONS


def find_accent_errors(text: str) -> list[tuple[str, str]]:
    """Busca palabras castellanas sin tilde en un texto.

    Devuelve una lista de tuplas (palabra_encontrada, forma_correcta)
    sin duplicados, manteniendo el orden de aparición.

    Args:
        text: Texto a inspeccionar.

    Returns:
        Lista de (incorrecto, correcto) sin duplicados.
    """
    if not text:
        return []

    seen = set()
    results = []

    for match in _WORDS_PATTERN.finditer(text):
        word = match.group(0)
        word_lower = word.lower()

        if word_lower not in seen:
            seen.add(word_lower)
            correct = ACCENT_WORDS[word_lower]
            results.append((word, correct))

    return results


def main():
    """Punto de entrada del hook.

    Lee el JSON de stdin, extrae el contenido escrito o editado,
    y busca palabras castellanas sin tilde. Si encuentra suficientes
    errores, emite un aviso por stderr.
    """
    try:
        data = json.load(sys.stdin)
    except ValueError as e:
        print(
            f"[spelling-guard] Aviso: no se pudo leer la entrada del hook: {e}. "
            f"La verificación ortográfica está desactivada para esta operación.",
            file=sys.stderr,
        )
        sys.exit(0)

    tool_input = data.get("tool_input", {})

    # Extraer la ruta del fichero
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "")

    if not should_inspect(file_path):
        sys.exit(0)

    # Extraer el contenido según la herramienta:
    # - Write: el campo 'content' contiene todo el fichero
    # - Edit: el campo 'new_string' contiene el texto de reemplazo
    content = tool_input.get("content", "") or tool_input.get("new_string", "")

    if not content:
        sys.exit(0)

    # Buscar errores de tildes
    errors = find_accent_errors(content)

    if len(errors) < MIN_FINDINGS:
        sys.exit(0)

    # Formatear la tabla de errores
    basename = os.path.basename(file_path)
    error_lines = "\n".join(
        f"  {wrong} -> {correct}" for wrong, correct in errors[:15]
    )

    remaining = len(errors) - 15
    if remaining > 0:
        error_lines += f"\n  ... y {remaining} más"

    print(
        f"\n"
        f"[El Rompe-cosas] Tildes ausentes en {basename}\n"
        f"\n"
        f"He detectado {len(errors)} palabra{'s' if len(errors) != 1 else ''}"
        f" sin tilde:\n"
        f"\n"
        f"{error_lines}\n"
        f"\n"
        f"Escribir bien no es opcional. Las tildes no son decoración:\n"
        f"cambian el significado de las palabras y restan credibilidad.\n"
        f"Corrige antes de seguir.\n",
        file=sys.stderr,
    )

    # No bloquear, solo informar
    sys.exit(0)


if __name__ == "__main__":
    main()
