from __future__ import annotations

import copy
import os
import pathlib

from src.models.server_config import LaunchConfig, Parameter
from src.utils.cross_platform import get_cpu_count


def _normalize_path(path: str) -> str:
    return str(pathlib.Path(path).expanduser().resolve())


def _validate_executable(path: str) -> bool:
    normalized = _normalize_path(path)
    p = pathlib.Path(normalized)
    if not p.is_file():
        return False
    if not os.access(normalized, os.X_OK):
        return False
    return True


class ParamService:
    PRESET_TEMPLATES: dict[str, list[Parameter]] = {
        "最小配置": [
            Parameter(name="-m", category="基础", required=True, value=None, description="模型文件路径"),
            Parameter(name="-c", category="基础", required=False, value="2048", description="上下文大小"),
        ],
        "GPU加速": [
            Parameter(name="-m", category="基础", required=True, value=None, description="模型文件路径"),
            Parameter(name="-c", category="基础", required=False, value="4096", description="上下文大小"),
            Parameter(name="-ngl", category="GPU", required=False, value="99", description="GPU层数"),
        ],
        "全功能": [
            Parameter(name="-m", category="基础", required=True, value=None, description="模型文件路径"),
            Parameter(name="-c", category="基础", required=False, value="4096", description="上下文大小"),
            Parameter(name="-ngl", category="GPU", required=False, value="99", description="GPU层数"),
            Parameter(name="--threads", category="性能", required=False, value="4", description="线程数"),
            Parameter(name="--host", category="网络", required=False, value="127.0.0.1", description="监听地址"),
            Parameter(name="--port", category="网络", required=False, value="8080", description="监听端口"),
        ],
    }

    def build_command(self, config: LaunchConfig) -> str:
        parts = [_normalize_path(config.server_path)]

        for param in config.parameters:
            if param.value:
                parts.extend([param.name, param.value])
            else:
                parts.append(param.name)

        return " ".join(parts)

    def get_template(self, name: str) -> list[Parameter]:
        if name not in self.PRESET_TEMPLATES:
            return []
        return copy.deepcopy(self.PRESET_TEMPLATES[name])

    def validate(self, config: LaunchConfig) -> list[str]:
        errors: list[str] = []

        if not _validate_executable(config.server_path):
            errors.append("服务器可执行文件不存在或不可执行")

        for param in config.parameters:
            if param.required and not param.value:
                errors.append(f"必填参数 {param.name} 的值为空")

        port_param = next(
            (p for p in config.parameters if p.name == "--port" and p.value),
            None,
        )
        if port_param:
            try:
                port = int(port_param.value)
                if port < 1 or port > 65535:
                    errors.append(f"端口号 {port_param.value} 超出范围")
            except ValueError:
                errors.append(f"端口号 {port_param.value} 超出范围")

        threads_param = next(
            (p for p in config.parameters if p.name == "--threads" and p.value),
            None,
        )
        if threads_param:
            try:
                threads = int(threads_param.value)
                max_threads = get_cpu_count()
                if threads < 1 or threads > max_threads:
                    errors.append(f"线程数 {threads_param.value} 超出范围")
            except ValueError:
                errors.append(f"线程数 {threads_param.value} 超出范围")

        return errors
