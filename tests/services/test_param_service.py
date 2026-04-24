import os
from unittest.mock import patch

import pytest

from src.models.server_config import LaunchConfig, Parameter
from src.services.param_service import ParamService


class TestBuildCommand:
    def setup_method(self):
        self.service = ParamService()

    def test_basic_command(self):
        cfg = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
            parameters=[
                Parameter(name="-m", category="基础", required=True, value="model.gguf"),
            ],
        )
        cmd = self.service.build_command(cfg)
        assert "/usr/bin/server" in cmd
        assert "-m model.gguf" in cmd

    def test_multiple_parameters(self):
        cfg = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
            parameters=[
                Parameter(name="-m", category="基础", required=True, value="model.gguf"),
                Parameter(name="-c", category="基础", required=False, value="4096"),
                Parameter(name="-ngl", category="GPU", required=False, value="99"),
            ],
        )
        cmd = self.service.build_command(cfg)
        assert "-m model.gguf" in cmd
        assert "-c 4096" in cmd
        assert "-ngl 99" in cmd

    def test_parameter_without_value(self):
        cfg = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
            parameters=[
                Parameter(name="--verbose", category="调试", required=False, value=None),
            ],
        )
        cmd = self.service.build_command(cfg)
        assert "--verbose" in cmd
        parts = cmd.split()
        assert "--verbose" in parts

    def test_empty_parameters(self):
        cfg = LaunchConfig(
            server_path="/usr/bin/server",
            shell_command="/usr/bin/server",
            parameters=[],
        )
        cmd = self.service.build_command(cfg)
        assert cmd.strip() == "/usr/bin/server"

    def test_path_normalization(self):
        cfg = LaunchConfig(
            server_path="~/bin/server",
            shell_command="~/bin/server",
            parameters=[],
        )
        cmd = self.service.build_command(cfg)
        assert "~" not in cmd
        assert os.path.isabs(cmd.strip())


class TestGetTemplate:
    def setup_method(self):
        self.service = ParamService()

    def test_exists_template_min(self):
        params, ssh_config = self.service.get_template("最小配置")
        assert len(params) == 2
        assert all(isinstance(p, Parameter) for p in params)
        assert ssh_config is None

    def test_exists_template_gpu(self):
        params, ssh_config = self.service.get_template("GPU加速")
        assert len(params) == 3
        names = [p.name for p in params]
        assert "-ngl" in names
        assert ssh_config is None

    def test_exists_template_full(self):
        params, ssh_config = self.service.get_template("全功能")
        assert len(params) == 6
        names = [p.name for p in params]
        assert "--threads" in names
        assert "--host" in names
        assert "--port" in names
        assert ssh_config is None

    def test_nonexistent_template(self):
        params, ssh_config = self.service.get_template("不存在")
        assert params == []
        assert ssh_config is None

    def test_deep_copy(self):
        params1, _ = self.service.get_template("最小配置")
        params2, _ = self.service.get_template("最小配置")
        params1[0].value = "modified"
        assert params2[0].value != "modified"

    def test_required_field(self):
        params, _ = self.service.get_template("最小配置")
        model_param = next(p for p in params if p.name == "-m")
        assert model_param.required is True

    def test_template_has_descriptions(self):
        params, _ = self.service.get_template("全功能")
        for p in params:
            assert isinstance(p.description, str)


class TestValidate:
    def setup_method(self):
        self.service = ParamService()

    def test_valid_executable_and_params(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="-m", category="基础", required=True, value="model.gguf"),
                ],
            )
            errors = self.service.validate(cfg)
            assert errors == []

    def test_invalid_executable(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=False
        ):
            cfg = LaunchConfig(
                server_path="/nonexistent",
                shell_command="/nonexistent",
                parameters=[],
            )
            errors = self.service.validate(cfg)
            assert len(errors) == 1
            assert "服务器可执行文件不存在或不可执行" in errors[0]

    def test_missing_required_param(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="-m", category="基础", required=True, value=None),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("-m" in e for e in errors)

    def test_empty_string_required_param(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="-m", category="基础", required=True, value=""),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("-m" in e for e in errors)

    def test_invalid_port_too_high(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--port", category="网络", required=False, value="99999"),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("端口号" in e for e in errors)

    def test_invalid_port_zero(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--port", category="网络", required=False, value="0"),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("端口号" in e for e in errors)

    def test_invalid_port_non_numeric(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--port", category="网络", required=False, value="abc"),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("端口号" in e for e in errors)

    def test_valid_port(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--port", category="网络", required=False, value="8080"),
                ],
            )
            errors = self.service.validate(cfg)
            assert not any("端口号" in e for e in errors)

    def test_invalid_threads_too_high(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ), patch(
            "src.services.param_service.get_cpu_count", return_value=4
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--threads", category="性能", required=False, value="99"),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("线程数" in e for e in errors)

    def test_invalid_threads_zero(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ), patch(
            "src.services.param_service.get_cpu_count", return_value=4
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--threads", category="性能", required=False, value="0"),
                ],
            )
            errors = self.service.validate(cfg)
            assert any("线程数" in e for e in errors)

    def test_valid_threads(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=True
        ), patch(
            "src.services.param_service.get_cpu_count", return_value=4
        ):
            cfg = LaunchConfig(
                server_path="/usr/bin/server",
                shell_command="/usr/bin/server",
                parameters=[
                    Parameter(name="--threads", category="性能", required=False, value="2"),
                ],
            )
            errors = self.service.validate(cfg)
            assert not any("线程数" in e for e in errors)

    def test_multiple_errors(self):
        with patch(
            "src.services.param_service._validate_executable", return_value=False
        ):
            cfg = LaunchConfig(
                server_path="/nonexistent",
                shell_command="/nonexistent",
                parameters=[
                    Parameter(name="-m", category="基础", required=True, value=None),
                ],
            )
            errors = self.service.validate(cfg)
            assert len(errors) >= 2
