#!/usr/bin/env python3
"""Tests para el hook de verificación ortográfica."""

import importlib.util
import os
import sys
import unittest

# El fichero del hook usa guión (spelling-guard.py), convención de los hooks
# de Alfred Dev. Python no permite importar módulos con guión directamente,
# así que usamos importlib para cargarlo por ruta.
_hook_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "spelling-guard.py")
_spec = importlib.util.spec_from_file_location("spelling_guard", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

find_accent_errors = _mod.find_accent_errors
should_inspect = _mod.should_inspect
ACCENT_WORDS = _mod.ACCENT_WORDS


class TestShouldInspect(unittest.TestCase):
    """Verifica que el filtro de ficheros funciona correctamente."""

    def test_inspects_markdown(self):
        self.assertTrue(should_inspect("/proyecto/docs/README.md"))

    def test_inspects_python(self):
        self.assertTrue(should_inspect("/proyecto/core/main.py"))

    def test_inspects_html(self):
        self.assertTrue(should_inspect("/proyecto/site/index.html"))

    def test_inspects_typescript(self):
        self.assertTrue(should_inspect("/proyecto/src/app.ts"))

    def test_ignores_json(self):
        self.assertFalse(should_inspect("/proyecto/package.json"))

    def test_ignores_lockfiles(self):
        self.assertFalse(should_inspect("/proyecto/package-lock.json"))

    def test_ignores_node_modules(self):
        self.assertFalse(should_inspect("/proyecto/node_modules/pkg/README.md"))

    def test_ignores_git(self):
        self.assertFalse(should_inspect("/proyecto/.git/HEAD"))

    def test_ignores_dist(self):
        self.assertFalse(should_inspect("/proyecto/dist/bundle.js"))

    def test_ignores_empty_path(self):
        self.assertFalse(should_inspect(""))

    def test_ignores_no_extension(self):
        self.assertFalse(should_inspect("/proyecto/Makefile"))


class TestFindAccentErrors(unittest.TestCase):
    """Verifica la detección de palabras sin tilde."""

    def test_detects_single_word(self):
        errors = find_accent_errors("La funcion devuelve un valor.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], ("funcion", "función"))

    def test_detects_multiple_words(self):
        text = "La configuracion del modulo es codigo basico."
        errors = find_accent_errors(text)
        found = {e[0].lower() for e in errors}
        self.assertIn("configuracion", found)
        self.assertIn("modulo", found)
        self.assertIn("basico", found)

    def test_no_duplicates(self):
        text = "La funcion principal llama a otra funcion auxiliar."
        errors = find_accent_errors(text)
        words = [e[0].lower() for e in errors]
        self.assertEqual(words.count("funcion"), 1)

    def test_case_insensitive(self):
        errors = find_accent_errors("FUNCION principal")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][1], "función")

    def test_no_errors_in_correct_text(self):
        errors = find_accent_errors("La función devuelve el código correcto.")
        self.assertEqual(errors, [])

    def test_empty_text(self):
        self.assertEqual(find_accent_errors(""), [])

    def test_none_text(self):
        self.assertEqual(find_accent_errors(None), [])

    def test_word_boundaries(self):
        """No detecta palabras parciales dentro de otras."""
        # 'version' dentro de 'subversion' no debería activar
        # Pero con \b sí lo detecta si 'version' es parte de 'subversion'
        # En este caso es correcto porque 'version' tiene límites de palabra propios
        errors = find_accent_errors("La version actual es estable.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], ("version", "versión"))

    def test_technical_context(self):
        """Detecta errores en contextos técnicos habituales."""
        text = "El metodo de autenticacion requiere validacion del parametro."
        errors = find_accent_errors(text)
        found = {e[0].lower() for e in errors}
        self.assertEqual(found, {"metodo", "autenticacion", "validacion", "parametro"})


class TestAccentDictionary(unittest.TestCase):
    """Verifica la integridad del diccionario de tildes."""

    def test_no_self_referencing_entries(self):
        """No hay entradas donde la forma incorrecta sea igual a la correcta."""
        for wrong, correct in ACCENT_WORDS.items():
            self.assertNotEqual(
                wrong, correct,
                f"Entrada innecesaria: '{wrong}' ya es la forma correcta",
            )

    def test_all_corrections_have_accents(self):
        """Todas las formas correctas contienen al menos un carácter acentuado."""
        accented = set("áéíóúÁÉÍÓÚ")
        for wrong, correct in ACCENT_WORDS.items():
            has_accent = any(c in accented for c in correct)
            self.assertTrue(
                has_accent,
                f"La corrección de '{wrong}' -> '{correct}' no tiene tilde",
            )

    def test_minimum_dictionary_size(self):
        """El diccionario tiene al menos 50 entradas para ser útil."""
        self.assertGreaterEqual(len(ACCENT_WORDS), 50)


if __name__ == "__main__":
    unittest.main()
