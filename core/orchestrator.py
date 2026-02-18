#!/usr/bin/env python3
"""
Orquestador de flujos del plugin Alfred Dev.

Este módulo gestiona el ciclo de vida completo de los flujos de trabajo
(feature, fix, spike, ship, audit). Cada flujo se compone de fases
secuenciales con gates de control que determinan si se puede avanzar
a la siguiente fase.

El orquestador se encarga de:
- Definir los flujos disponibles y sus fases.
- Crear y gestionar sesiones de trabajo.
- Evaluar las gates de cada fase para decidir si se aprueba el avance.
- Persistir y recuperar el estado de las sesiones en disco.

Arquitectura de gates:
    Las gates actúan como puntos de control entre fases. Su comportamiento
    depende del tipo definido en cada fase: las gates de tipo «usuario»
    requieren aprobación explícita; las «automático» se evalúan contra
    métricas objetivas como tests verdes o pipeline OK; las combinadas
    (ej. «automático+seguridad») acumulan ambas condiciones.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# --- Constantes de tipos de gate -------------------------------------------
# Se extraen como constantes para evitar la duplicación de literales
# y facilitar la validación centralizada.

GATE_USUARIO = "usuario"
GATE_AUTOMATICO = "automatico"
GATE_LIBRE = "libre"
GATE_USUARIO_SEGURIDAD = "usuario+seguridad"
GATE_AUTOMATICO_SEGURIDAD = "automatico+seguridad"

_KNOWN_GATE_TYPES = {
    GATE_LIBRE, GATE_USUARIO, GATE_AUTOMATICO,
    GATE_USUARIO_SEGURIDAD, GATE_AUTOMATICO_SEGURIDAD,
}

# --- Definición de flujos ---------------------------------------------------
# Cada flujo describe una secuencia de fases que el orquestador recorre.
# Los agentes listados en cada fase son los responsables de ejecutarla.

FLOWS: Dict[str, Dict[str, Any]] = {
    "feature": {
        "nombre": "feature",
        "fases": [
            {
                "nombre": "producto",
                "agentes": ["product-owner"],
                "paralelo": False,
                "gate": "gate_producto",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Análisis de requisitos y definición del alcance "
                    "funcional de la nueva característica."
                ),
            },
            {
                "nombre": "arquitectura",
                "agentes": ["architect", "security-officer"],
                "paralelo": True,
                "gate": "gate_arquitectura",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Diseño técnico, elección de patrones y validación "
                    "de la propuesta arquitectónica con threat model."
                ),
            },
            {
                "nombre": "desarrollo",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_desarrollo",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": (
                    "Implementación del código siguiendo TDD estricto "
                    "con ciclos rojo-verde-refactor."
                ),
            },
            {
                "nombre": "calidad",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_calidad",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Revisión de calidad, ejecución de tests y "
                    "auditoría de seguridad en paralelo."
                ),
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion",
                "gate_tipo": GATE_LIBRE,
                "descripcion": (
                    "Generación de documentación técnica y de usuario "
                    "para la comunidad."
                ),
            },
            {
                "nombre": "entrega",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_entrega",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "descripcion": (
                    "Preparación del entregable, changelog y "
                    "validación final antes del merge."
                ),
            },
        ],
    },
    "fix": {
        "nombre": "fix",
        "fases": [
            {
                "nombre": "diagnostico",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_diagnostico",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Identificación de la causa raíz del bug "
                    "mediante análisis de logs, trazas y reproducción."
                ),
            },
            {
                "nombre": "correccion",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_correccion",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": (
                    "Aplicación del fix con test de regresión "
                    "que demuestre que el bug queda resuelto."
                ),
            },
            {
                "nombre": "validacion",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_validacion",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Validación completa: tests de regresión, "
                    "suite existente y revisión de seguridad."
                ),
            },
        ],
    },
    "spike": {
        "nombre": "spike",
        "fases": [
            {
                "nombre": "exploracion",
                "agentes": ["architect", "senior-dev"],
                "paralelo": True,
                "gate": "gate_exploracion",
                "gate_tipo": GATE_LIBRE,
                "descripcion": (
                    "Investigación exploratoria: pruebas de concepto, "
                    "benchmarks y evaluación de alternativas."
                ),
            },
            {
                "nombre": "conclusiones",
                "agentes": ["architect"],
                "paralelo": False,
                "gate": "gate_conclusiones",
                "gate_tipo": GATE_USUARIO,
                "descripcion": (
                    "Consolidación de hallazgos en un informe "
                    "con recomendaciones accionables."
                ),
            },
        ],
    },
    "ship": {
        "nombre": "ship",
        "fases": [
            {
                "nombre": "auditoria_final",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_auditoria_final",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Auditoría completa de calidad y seguridad "
                    "antes de la release."
                ),
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion_ship",
                "gate_tipo": GATE_LIBRE,
                "descripcion": (
                    "Actualización de la documentación de release, "
                    "changelog y guías de migración."
                ),
            },
            {
                "nombre": "empaquetado",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_empaquetado",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": (
                    "Generación del artefacto de release, "
                    "versionado semántico y etiquetado."
                ),
            },
            {
                "nombre": "despliegue",
                "agentes": ["devops-engineer"],
                "paralelo": False,
                "gate": "gate_despliegue",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "descripcion": (
                    "Despliegue a producción con validación "
                    "post-deploy y rollback preparado."
                ),
            },
        ],
    },
    "audit": {
        "nombre": "audit",
        "fases": [
            {
                "nombre": "auditoria_paralela",
                "agentes": [
                    "qa-engineer",
                    "security-officer",
                    "architect",
                    "tech-writer",
                ],
                "paralelo": True,
                "gate": "gate_auditoria",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": (
                    "Auditoría completa del código en paralelo: "
                    "calidad, seguridad, arquitectura "
                    "y documentación."
                ),
            },
        ],
    },
}


def create_session(command: str, description: str) -> Dict[str, Any]:
    """
    Crea una nueva sesión de trabajo para el flujo indicado.

    La sesión contiene todo el estado necesario para que el orquestador
    sepa en qué punto del flujo se encuentra el usuario y qué fases
    se han completado.

    Args:
        command: Identificador del flujo (feature, fix, spike, ship, audit).
        description: Descripción en lenguaje natural de la tarea.

    Returns:
        Diccionario con el estado inicial de la sesión.

    Raises:
        ValueError: Si el comando no corresponde a ningún flujo definido.
    """
    if command not in FLOWS:
        raise ValueError(
            f"Flujo '{command}' no reconocido. "
            f"Flujos disponibles: {', '.join(FLOWS.keys())}"
        )

    flow = FLOWS[command]
    primera_fase = flow["fases"][0]["nombre"]

    return {
        "comando": command,
        "descripcion": description,
        "fase_actual": primera_fase,
        "fase_numero": 0,
        "fases_completadas": [],
        "artefactos": [],
        "creado_en": datetime.now(timezone.utc).isoformat(),
        "actualizado_en": datetime.now(timezone.utc).isoformat(),
    }


def check_gate(
    session: Dict[str, Any],
    resultado: str = "",
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """
    Evalúa la gate de la fase actual para decidir si se puede avanzar.

    La lógica de evaluación depende del tipo de gate definido en la fase:
    - «usuario»: requiere resultado «aprobado».
    - «automático»: requiere resultado «aprobado» y tests verdes.
    - «usuario+seguridad»: requiere aprobación del usuario y seguridad OK.
    - «automático+seguridad»: requiere tests, seguridad y resultado OK.
    - «libre»: se aprueba siempre que el resultado sea «aprobado».

    Args:
        session: Estado actual de la sesión.
        resultado: Resultado reportado (normalmente «aprobado» o «rechazado»).
        security_ok: Indica si la auditoría de seguridad es favorable.
        tests_ok: Indica si los tests pasan correctamente.

    Returns:
        Diccionario con las claves «passed» (bool) y «reason» (str).
    """
    comando = session["comando"]
    if comando not in FLOWS:
        return {"passed": False, "reason": f"Flujo '{comando}' no definido en FLOWS."}

    flow = FLOWS[comando]
    fase_numero = session["fase_numero"]
    fase = flow["fases"][fase_numero]
    gate_tipo = fase["gate_tipo"]

    # Se acumulan las condiciones que debe cumplir la gate.
    # El orden de comprobación determina qué error se reporta primero.
    failures = []

    requires_tests = "automatico" in gate_tipo
    requires_security = "seguridad" in gate_tipo
    requires_approval = gate_tipo in (GATE_USUARIO, GATE_USUARIO_SEGURIDAD)
    is_known = gate_tipo in _KNOWN_GATE_TYPES

    if not is_known:
        return {"passed": False, "reason": f"Tipo de gate desconocido: {gate_tipo}"}

    if requires_tests and not tests_ok:
        failures.append("Los tests no pasan.")
    if requires_security and not security_ok:
        failures.append("La auditoría de seguridad no es favorable.")
    if resultado != "aprobado":
        if requires_approval:
            failures.append("Aprobación del usuario requerida.")
        else:
            failures.append("El resultado no es favorable.")

    passed = len(failures) == 0
    reason = failures[0] if failures else ""

    return {"passed": passed, "reason": reason}


def advance_phase(
    session: Dict[str, Any],
    resultado: str = "aprobado",
    artefactos: Optional[List[str]] = None,
    security_ok: bool = True,
    tests_ok: bool = True,
) -> Dict[str, Any]:
    """
    Intenta avanzar la sesión a la siguiente fase del flujo.

    Primero evalúa la gate de la fase actual. Si la gate se supera,
    registra la fase como completada y actualiza el puntero a la
    siguiente. Si ya no quedan fases, marca la sesión como «completado».

    Args:
        session: Estado actual de la sesión.
        resultado: Resultado a evaluar en la gate (por defecto «aprobado»).
        artefactos: Lista opcional de artefactos generados en la fase.
        security_ok: Indica si la auditoría de seguridad es favorable.
        tests_ok: Indica si los tests pasan correctamente.

    Returns:
        Diccionario con el estado actualizado de la sesión.

    Raises:
        RuntimeError: Si la gate de la fase actual no se supera.
    """
    if artefactos is None:
        artefactos = []

    comando = session["comando"]
    if comando not in FLOWS:
        raise RuntimeError(f"Flujo '{comando}' no definido en FLOWS.")

    flow = FLOWS[comando]
    fases = flow["fases"]

    # Si ya está completado, devolver sin cambios
    if session["fase_actual"] == "completado":
        return session

    # Evaluar la gate de la fase actual propagando todos los parámetros
    gate_result = check_gate(
        session, resultado=resultado, security_ok=security_ok, tests_ok=tests_ok
    )
    if not gate_result["passed"]:
        raise RuntimeError(
            f"No se puede avanzar: {gate_result['reason']}"
        )

    # Registrar la fase completada
    fase_completada = {
        "nombre": fases[session["fase_numero"]]["nombre"],
        "resultado": resultado,
        "artefactos": artefactos,
        "completada_en": datetime.now(timezone.utc).isoformat(),
    }
    session["fases_completadas"].append(fase_completada)

    # Incorporar artefactos al registro global de la sesión
    session["artefactos"].extend(artefactos)

    # Avanzar al siguiente índice
    siguiente = session["fase_numero"] + 1

    if siguiente < len(fases):
        session["fase_numero"] = siguiente
        session["fase_actual"] = fases[siguiente]["nombre"]
    else:
        # No quedan más fases: el flujo está completado
        session["fase_actual"] = "completado"
        session["fase_numero"] = siguiente

    session["actualizado_en"] = datetime.now(timezone.utc).isoformat()
    return session


def save_state(session: Dict[str, Any], state_path: str) -> None:
    """
    Persiste el estado de la sesión en un fichero JSON.

    Se utiliza escritura atómica (escritura + renombrado) para evitar
    corrupción si el proceso se interrumpe a mitad de escritura. Si la
    operación falla, se limpia el fichero temporal y se relanza el error
    como RuntimeError para que el llamante sepa que el estado no se guardó.

    Args:
        session: Estado de la sesión a guardar.
        state_path: Ruta absoluta del fichero de destino.

    Raises:
        RuntimeError: Si no se puede guardar el estado por cualquier razón.
    """
    tmp_path = state_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
        # Renombrado atómico en sistemas POSIX
        os.replace(tmp_path, state_path)
    except (OSError, TypeError) as e:
        # Limpiar el fichero temporal si quedó huérfano
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError as cleanup_err:
                print(
                    f"[Alfred Dev] Aviso: no se pudo limpiar el fichero temporal "
                    f"'{tmp_path}': {cleanup_err}",
                    file=sys.stderr,
                )
        raise RuntimeError(
            f"No se pudo guardar el estado de sesión en '{state_path}': {e}"
        ) from e


# Claves mínimas que debe tener un estado de sesión válido
_REQUIRED_STATE_KEYS = {"comando", "fase_actual", "fase_numero"}


def load_state(state_path: str) -> Optional[Dict[str, Any]]:
    """
    Carga el estado de una sesión desde un fichero JSON.

    Distingue entre tres situaciones:
    - Fichero ausente: devuelve None silenciosamente (caso normal).
    - Fichero corrupto o ilegible: devuelve None pero avisa en stderr.
    - Fichero con estructura inválida: devuelve None y avisa en stderr.

    Args:
        state_path: Ruta absoluta del fichero a leer.

    Returns:
        Diccionario con el estado de la sesión, o None si el fichero
        no existe, está corrupto o tiene estructura inválida.
    """
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(
            f"[Alfred Dev] Error: el fichero de estado '{state_path}' está corrupto: {e}",
            file=sys.stderr,
        )
        return None
    except OSError as e:
        print(
            f"[Alfred Dev] Error al leer el estado de sesión '{state_path}': {e}",
            file=sys.stderr,
        )
        return None

    # Validar estructura mínima: presencia de claves obligatorias
    if not isinstance(data, dict) or not _REQUIRED_STATE_KEYS.issubset(data.keys()):
        print(
            f"[Alfred Dev] Aviso: el fichero de estado '{state_path}' tiene una "
            f"estructura inesperada (faltan claves obligatorias). Se ignorará.",
            file=sys.stderr,
        )
        return None

    # Validar tipos de las claves obligatorias para evitar TypeError
    # en comparaciones posteriores (ej.: fase_numero >= len(fases))
    if not isinstance(data.get("comando"), str):
        print(
            f"[Alfred Dev] Aviso: 'comando' no es un string en '{state_path}'. Se ignorará.",
            file=sys.stderr,
        )
        return None
    if not isinstance(data.get("fase_actual"), str):
        print(
            f"[Alfred Dev] Aviso: 'fase_actual' no es un string en '{state_path}'. Se ignorará.",
            file=sys.stderr,
        )
        return None
    if not isinstance(data.get("fase_numero"), int):
        print(
            f"[Alfred Dev] Aviso: 'fase_numero' no es un entero en '{state_path}'. Se ignorará.",
            file=sys.stderr,
        )
        return None

    return data
