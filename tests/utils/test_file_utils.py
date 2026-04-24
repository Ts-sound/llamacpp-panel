import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.file_utils import normalize_path, validate_executable


class TestNormalizePath:
    def test_basic_path(self):
        assert normalize_path("/usr/bin/server") == "/usr/bin/server"

    def test_tilde_expansion(self):
        result = normalize_path("~/test")
        assert result.startswith("/")
        assert "~" not in result

    def test_relative_path(self):
        result = normalize_path("relative/path")
        assert os.path.isabs(result)

    def test_dot_resolution(self):
        result = normalize_path("/usr/./bin/server")
        assert "/./" not in result
        assert result == "/usr/bin/server"

    def test_dotdot_resolution(self):
        result = normalize_path("/usr/local/../bin/server")
        assert "/../" not in result
        assert result == "/usr/bin/server"

    def test_trailing_slash(self):
        result = normalize_path("/usr/bin/")
        assert not result.endswith("/")

    def test_returns_string(self):
        result = normalize_path("/usr/bin/server")
        assert isinstance(result, str)


class TestValidateExecutable:
    def test_valid_executable(self, tmp_path):
        exe = tmp_path / "server"
        exe.write_text("#!/bin/sh\necho hi", encoding="utf-8")
        exe.chmod(0o755)

        assert validate_executable(str(exe)) is True

    def test_nonexistent_file(self, tmp_path):
        assert validate_executable(str(tmp_path / "nonexistent")) is False

    def test_not_executable(self, tmp_path):
        f = tmp_path / "not_exec"
        f.write_text("content", encoding="utf-8")
        f.chmod(0o644)

        assert validate_executable(str(f)) is False

    def test_directory_not_valid(self, tmp_path):
        assert validate_executable(str(tmp_path)) is False

    def test_relative_path(self, tmp_path):
        exe = tmp_path / "server"
        exe.write_text("#!/bin/sh", encoding="utf-8")
        exe.chmod(0o755)

        orig = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert validate_executable("server") is True
        finally:
            os.chdir(orig)

    def test_empty_string(self):
        assert validate_executable("") is False
