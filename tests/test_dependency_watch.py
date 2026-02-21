#!/usr/bin/env python3
"""Tests para el hook dependency-watch.py."""

import importlib.util
import os
import unittest

# Importar el hook usando importlib (el nombre tiene guion)
_hook_path = os.path.join(os.path.dirname(__file__), "..", "hooks", "dependency-watch.py")
_spec = importlib.util.spec_from_file_location("dependency_watch", _hook_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

is_dependency_file = _mod.is_dependency_file


class TestIsDependencyFile(unittest.TestCase):
    """Verifica que los ficheros de dependencias se detectan correctamente."""

    # --- Casos positivos: ficheros de dependencias ---

    def test_package_json(self):
        self.assertTrue(is_dependency_file("/proyecto/package.json"))

    def test_package_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/package-lock.json"))

    def test_yarn_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/yarn.lock"))

    def test_pnpm_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/pnpm-lock.yaml"))

    def test_pyproject_toml(self):
        self.assertTrue(is_dependency_file("/proyecto/pyproject.toml"))

    def test_requirements_txt(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements.txt"))

    def test_requirements_dev(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements-dev.txt"))

    def test_requirements_ci(self):
        self.assertTrue(is_dependency_file("/proyecto/requirements-ci.txt"))

    def test_cargo_toml(self):
        self.assertTrue(is_dependency_file("/proyecto/Cargo.toml"))

    def test_cargo_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/Cargo.lock"))

    def test_go_mod(self):
        self.assertTrue(is_dependency_file("/proyecto/go.mod"))

    def test_go_sum(self):
        self.assertTrue(is_dependency_file("/proyecto/go.sum"))

    def test_gemfile(self):
        self.assertTrue(is_dependency_file("/proyecto/Gemfile"))

    def test_gemfile_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/Gemfile.lock"))

    def test_pom_xml(self):
        self.assertTrue(is_dependency_file("/proyecto/pom.xml"))

    def test_build_gradle(self):
        self.assertTrue(is_dependency_file("/proyecto/build.gradle"))

    def test_csproj(self):
        self.assertTrue(is_dependency_file("/proyecto/MiApp.csproj"))

    def test_fsproj(self):
        self.assertTrue(is_dependency_file("/proyecto/MiApp.fsproj"))

    def test_composer_json(self):
        self.assertTrue(is_dependency_file("/proyecto/composer.json"))

    def test_mix_exs(self):
        self.assertTrue(is_dependency_file("/proyecto/mix.exs"))

    def test_pipfile(self):
        self.assertTrue(is_dependency_file("/proyecto/Pipfile"))

    def test_poetry_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/poetry.lock"))

    def test_uv_lock(self):
        self.assertTrue(is_dependency_file("/proyecto/uv.lock"))

    # --- Casos negativos: ficheros normales ---

    def test_readme(self):
        self.assertFalse(is_dependency_file("/proyecto/README.md"))

    def test_source_file(self):
        self.assertFalse(is_dependency_file("/proyecto/src/main.py"))

    def test_config_file(self):
        self.assertFalse(is_dependency_file("/proyecto/.eslintrc.json"))

    def test_tsconfig(self):
        self.assertFalse(is_dependency_file("/proyecto/tsconfig.json"))

    def test_gitignore(self):
        self.assertFalse(is_dependency_file("/proyecto/.gitignore"))


if __name__ == "__main__":
    unittest.main()
