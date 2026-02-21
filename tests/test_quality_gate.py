#!/usr/bin/env python3
"""Tests para el hook quality-gate.py."""

import importlib.util
import os
import unittest

# Importar el hook usando importlib (el nombre tiene guion)
_hook_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "quality-gate.py")
_spec = importlib.util.spec_from_file_location("quality_gate", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

is_test_command = _mod.is_test_command
has_failures = _mod.has_failures


class TestIsTestCommand(unittest.TestCase):
    """Verifica que los runners de tests se detectan correctamente."""

    def test_pytest(self):
        self.assertTrue(is_test_command("pytest tests/"))

    def test_python_m_pytest(self):
        self.assertTrue(is_test_command("python -m pytest tests/ -v"))

    def test_jest(self):
        self.assertTrue(is_test_command("jest --coverage"))

    def test_vitest(self):
        self.assertTrue(is_test_command("vitest run"))

    def test_cargo_test(self):
        self.assertTrue(is_test_command("cargo test"))

    def test_go_test(self):
        self.assertTrue(is_test_command("go test ./..."))

    def test_npm_test(self):
        self.assertTrue(is_test_command("npm test"))

    def test_npm_run_test(self):
        self.assertTrue(is_test_command("npm run test"))

    def test_bun_test(self):
        self.assertTrue(is_test_command("bun test"))

    def test_rspec(self):
        self.assertTrue(is_test_command("rspec spec/"))

    def test_mix_test(self):
        self.assertTrue(is_test_command("mix test"))

    def test_not_test_command_ls(self):
        self.assertFalse(is_test_command("ls -la"))

    def test_not_test_command_grep(self):
        self.assertFalse(is_test_command("grep pytest config.ini"))

    def test_not_test_command_cat(self):
        self.assertFalse(is_test_command("cat pytest.ini"))

    def test_not_test_command_git(self):
        self.assertFalse(is_test_command("git commit -m 'fix tests'"))


class TestHasFailures(unittest.TestCase):
    """Verifica que la deteccion de fallos funciona correctamente."""

    def test_detects_FAIL(self):
        self.assertTrue(has_failures("FAIL tests/test_foo.py"))

    def test_detects_FAILED(self):
        self.assertTrue(has_failures("FAILED test_something"))

    def test_detects_failures(self):
        self.assertTrue(has_failures("2 failures, 1 error"))

    def test_detects_n_failed(self):
        self.assertTrue(has_failures("3 failed, 2 passed"))

    def test_detects_tests_failed(self):
        self.assertTrue(has_failures("Tests failed: 1"))

    def test_detects_assertion_error(self):
        self.assertTrue(has_failures("AssertionError: expected True"))

    def test_detects_mixed_case_fail(self):
        """Verifica que 'Fail' con case mixto tambien se detecta."""
        self.assertTrue(has_failures("Fail: test_something"))

    def test_detects_mixed_case_failure(self):
        """Verifica que 'Test Failure' se detecta con case mixto."""
        self.assertTrue(has_failures("Test Failure in module X"))

    def test_passing_output(self):
        self.assertFalse(has_failures("All 42 tests passed"))

    def test_empty_output(self):
        self.assertFalse(has_failures(""))

    def test_normal_output(self):
        self.assertFalse(has_failures("Compiling project...\nDone."))


if __name__ == "__main__":
    unittest.main()
