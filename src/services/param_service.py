from __future__ import annotations

import copy
import json
import logging
import os
import pathlib
from typing import Any

from src.models.server_config import LaunchConfig, Parameter
from src.models.ssh_config import SSHConfig
from src.utils.cross_platform import get_cpu_count

logger = logging.getLogger(__name__)


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


DEFAULT_TEMPLATES: dict[str, list[Parameter]] = {
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

TEMPLATE_DIR = "config/templates"


class ParamService:
    def __init__(self) -> None:
        self._user_templates: dict[str, tuple[list[Parameter], SSHConfig | None]] = {}
        self._template_dir = pathlib.Path(TEMPLATE_DIR)
        self._template_dir.mkdir(parents=True, exist_ok=True)
        self._load_user_templates()

    def _load_user_templates(self) -> None:
        for f in self._template_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                name = data.get("name", f.stem)
                params = [
                    Parameter(
                        name=p["name"],
                        category=p.get("category", ""),
                        required=p.get("required", False),
                        value=p.get("value"),
                        description=p.get("description", ""),
                    )
                    for p in data.get("parameters", [])
                ]
                ssh_config = None
                if "ssh_config" in data:
                    ssh_data = data["ssh_config"]
                    ssh_config = SSHConfig(
                        local_port=ssh_data.get("local_port", 8080),
                        remote_port=ssh_data.get("remote_port", 8080),
                        remote_host=ssh_data.get("remote_host", ""),
                        username=ssh_data.get("username", "root"),
                        ssh_port=ssh_data.get("ssh_port", 22),
                        key_file=ssh_data.get("key_file", ""),
                    )
                self._user_templates[name] = (params, ssh_config)
                logger.info("[LOAD_TEMPLATE] name=%s, params=%d, ssh=%s", 
                            name, len(params), ssh_config is not None)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("[LOAD_TEMPLATE] error: %s, file=%s", e, f)
                continue

    def get_template_names(self) -> list[str]:
        all_names = set(DEFAULT_TEMPLATES.keys()) | set(self._user_templates.keys())
        result = sorted(all_names)
        logger.debug("[GET_TEMPLATE_NAMES] count=%d, names=%s", len(result), result)
        return result

    def get_template(self, name: str) -> tuple[list[Parameter], SSHConfig | None]:
        logger.info("[GET_TEMPLATE] name=%s", name)
        
        if name in self._user_templates:
            params, ssh_config = self._user_templates[name]
            params_copy = copy.deepcopy(params)
            ssh_copy = copy.deepcopy(ssh_config) if ssh_config else None
            logger.info("[GET_TEMPLATE] found_user_template: params=%d, ssh=%s", 
                        len(params_copy), ssh_copy is not None)
            return params_copy, ssh_copy
        if name in DEFAULT_TEMPLATES:
            params = copy.deepcopy(DEFAULT_TEMPLATES[name])
            logger.info("[GET_TEMPLATE] found_default_template: params=%d, ssh=None", len(params))
            return params, None
        
        logger.warning("[GET_TEMPLATE] not_found: name=%s", name)
        return [], None

    def save_template(
        self, 
        name: str, 
        params: list[Parameter], 
        ssh_config: SSHConfig | None = None,
    ) -> None:
        logger.info("[SAVE_TEMPLATE] name=%s, params=%d, ssh=%s", 
                    name, len(params), ssh_config is not None)
        
        data: dict[str, Any] = {
            "name": name,
            "parameters": [
                {
                    "name": p.name,
                    "category": p.category,
                    "required": p.required,
                    "value": p.value,
                    "description": p.description,
                }
                for p in params
            ],
        }
        if ssh_config:
            data["ssh_config"] = {
                "local_port": ssh_config.local_port,
                "remote_port": ssh_config.remote_port,
                "remote_host": ssh_config.remote_host,
                "username": ssh_config.username,
                "ssh_port": ssh_config.ssh_port,
                "key_file": ssh_config.key_file,
            }
        
        target = self._template_dir / f"{name}.json"
        logger.debug("[SAVE_TEMPLATE] target_path=%s", target)
        
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        
        self._user_templates[name] = (copy.deepcopy(params), copy.deepcopy(ssh_config) if ssh_config else None)
        logger.info("[SAVE_TEMPLATE] success: %s", target)

    def build_command(self, config: LaunchConfig) -> str:
        logger.info("[BUILD_CMD] server_path=%s", config.server_path)
        
        parts = [_normalize_path(config.server_path)]
        
        for param in config.parameters:
            logger.debug("[BUILD_CMD] param: name=%s, value=%s, required=%s", 
                         param.name, param.value, param.required)
            if param.value:
                parts.extend([param.name, param.value])
            else:
                parts.append(param.name)
        
        command = " ".join(parts)
        logger.info("[BUILD_CMD] result=%s", command)
        return command

    def validate(self, config: LaunchConfig) -> list[str]:
        logger.info("[VALIDATE] server_path=%s, param_count=%d", 
                    config.server_path, len(config.parameters))
        errors: list[str] = []

        if not _validate_executable(config.server_path):
            logger.warning("[VALIDATE] executable_invalid: %s", config.server_path)
            errors.append("服务器可执行文件不存在或不可执行")

        for param in config.parameters:
            if param.required and not param.value:
                logger.warning("[VALIDATE] required_param_missing: name=%s", param.name)
                errors.append(f"必填参数 {param.name} 的值为空")

        port_param = next(
            (p for p in config.parameters if p.name == "--port" and p.value),
            None,
        )
        if port_param:
            try:
                port = int(port_param.value)
                if port < 1 or port > 65535:
                    logger.warning("[VALIDATE] port_out_of_range: %s", port_param.value)
                    errors.append(f"端口号 {port_param.value} 超出范围")
            except ValueError:
                logger.warning("[VALIDATE] port_invalid: %s", port_param.value)
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
                    logger.warning("[VALIDATE] threads_out_of_range: %s (max=%d)", 
                                   threads_param.value, max_threads)
                    errors.append(f"线程数 {threads_param.value} 超出范围")
            except ValueError:
                logger.warning("[VALIDATE] threads_invalid: %s", threads_param.value)
                errors.append(f"线程数 {threads_param.value} 超出范围")

        logger.info("[VALIDATE] result: error_count=%d, errors=%s", len(errors), errors)
        return errors
