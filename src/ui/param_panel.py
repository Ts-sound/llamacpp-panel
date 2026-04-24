from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from src.models.server_config import LaunchConfig, Parameter
from src.services.config_service import ConfigService
from src.services.param_service import ParamService
from src.utils.file_utils import select_server_file


class ParamPanel(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        param_service: ParamService,
        config_service: ConfigService,
    ) -> None:
        super().__init__(master)
        self._param_service = param_service
        self._config_service = config_service
        self._parameters: list[Parameter] = []
        self._server_path: str = ""
        self._model_path: str = ""

        self._on_file_selected: Callable[[str], None] = lambda p: None
        self._on_model_selected: Callable[[str], None] = lambda p: None
        self._on_load_template: Callable[[str], None] = lambda n: None
        self._on_save_template: Callable[[str], None] = lambda n: None
        self._on_save_as_template: Callable[[str], None] = lambda n: None
        self._on_parameter_changed: Callable[[list[Parameter]], None] = lambda p: None

        self._build_ui()

    def _build_ui(self) -> None:
        self._file_row = FileSelectRow(self)
        self._template_row = TemplateRow(self, self._param_service)
        self._model_row = ModelSelectRow(self)
        self._param_table = ParamTable(self)
        self._cmd_preview = CmdPreviewRow(self)

        add_btn = ttk.Button(self, text="+ 添加参数", command=self._on_add_parameter)

        self._file_row.pack(fill=tk.X, padx=5, pady=(5, 0))
        self._template_row.pack(fill=tk.X, padx=5, pady=5)
        self._model_row.pack(fill=tk.X, padx=5, pady=5)
        self._param_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        add_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        self._cmd_preview.pack(fill=tk.X, padx=5, pady=(0, 5))

        self._file_row.on_select_file = self._on_select_file
        self._model_row.on_select = self._handle_model_selected
        self._template_row.on_load = self._on_load_template_clicked
        self._template_row.on_save = self._on_save_template_clicked
        self._template_row.on_save_as = self._on_save_as_template_clicked
        self._cmd_preview.on_copy = self._on_copy_command

    def _on_select_file(self) -> None:
        path = select_server_file(self)
        if not path:
            return
        self._server_path = path
        self._file_row.set_path(path)
        self._on_file_selected(path)

    def _handle_model_selected(self, path: str) -> None:
        self._model_path = path
        self._model_row.set_model(path)
        self._on_model_selected(path)
        self.update_command_preview()

    def _on_load_template_clicked(self) -> None:
        name = self._template_row.get_selected_template()
        if not name:
            return
        params = self._param_service.get_template(name)
        self.load_parameters(params)
        self._on_load_template(name)

    def _on_save_template_clicked(self) -> None:
        name = self._template_row.get_selected_template()
        if not name:
            messagebox.showwarning("警告", "请先选择一个模板")
            return
        self._on_save_template(name)

    def _on_save_as_template_clicked(self) -> None:
        self._on_save_as_template()

    def _on_add_parameter(self) -> None:
        param = Parameter(name="", value="", category="other", required=False)
        self._parameters.append(param)
        self._param_table.insert_param(param)
        self._on_parameter_changed(self._parameters)

    def _on_copy_command(self) -> None:
        cmd = self._cmd_preview.get_preview()
        self.clipboard_clear()
        self.clipboard_append(cmd)
        self._cmd_preview.show_copied()

    def load_parameters(self, params: list[Parameter]) -> None:
        non_model_params = [p for p in params if p.name != "-m"]
        self._parameters = non_model_params
        self._param_table.clear()
        for p in non_model_params:
            self._param_table.insert_param(p)
        self.update_command_preview()

    def get_current_params(self) -> list[Parameter]:
        return list(self._parameters)

    def get_launch_config(self) -> LaunchConfig:
        params = list(self._parameters)
        if self._model_path:
            params.insert(0, Parameter(
                name="-m",
                value=self._model_path,
                category="model",
                required=True,
                description="模型路径",
            ))
        cmd = self._param_service.build_command(LaunchConfig(
            server_path=self._server_path,
            parameters=params,
            selected_template=self._template_row.get_selected_template(),
            shell_command="",
        ))
        return LaunchConfig(
            server_path=self._server_path,
            shell_command=cmd,
            parameters=params,
            selected_template=self._template_row.get_selected_template(),
        )

    def update_command_preview(self) -> None:
        params = list(self._parameters)
        if self._model_path:
            params.insert(0, Parameter(
                name="-m",
                value=self._model_path,
                category="model",
                required=True,
                description="模型路径",
            ))
        config = LaunchConfig(
            server_path=self._server_path,
            shell_command="",
            parameters=params,
        )
        cmd = self._param_service.build_command(config)
        self._cmd_preview.set_preview(cmd)

    def set_server_path(self, path: str) -> None:
        self._server_path = path
        self._file_row.set_path(path)

    def set_model_path(self, path: str) -> None:
        self._model_path = path
        self._model_row.set_model(path)

    def get_server_path(self) -> str:
        return self._server_path

    def get_model_path(self) -> str:
        return self._model_path


class FileSelectRow(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.on_select_file: Callable[[], None] = lambda: None

        self.btn_select_file = ttk.Button(self, text="选择启动文件", command=self._on_click)
        self.lbl_server_path = ttk.Label(self, text="未选择")

        self.btn_select_file.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_server_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _on_click(self) -> None:
        self.on_select_file()

    def set_path(self, path: str) -> None:
        display = path
        if len(display) > 60:
            display = "..." + display[-57:]
        self.lbl_server_path.config(text=display)


class TemplateRow(ttk.Frame):
    def __init__(self, master: tk.Misc, param_service: ParamService) -> None:
        super().__init__(master)
        self._param_service = param_service
        self.on_load: Callable[[], None] = lambda: None
        self.on_save: Callable[[], None] = lambda: None
        self.on_save_as: Callable[[], None] = lambda: None

        ttk.Label(self, text="模板:").pack(side=tk.LEFT, padx=(0, 2))

        self.cmb_template = ttk.Combobox(
            self,
            values=param_service.get_template_names(),
            state="readonly",
            width=15,
        )
        self.cmb_template.pack(side=tk.LEFT, padx=(0, 5))
        if self.cmb_template["values"]:
            self.cmb_template.current(0)

        self.btn_load = ttk.Button(self, text="加载", command=self._on_load, width=6)
        self.btn_save = ttk.Button(self, text="保存", command=self._on_save, width=6)
        self.btn_save_as = ttk.Button(
            self, text="另存为", command=self._on_save_as, width=6
        )

        self.btn_load.pack(side=tk.LEFT, padx=2)
        self.btn_save.pack(side=tk.LEFT, padx=2)
        self.btn_save_as.pack(side=tk.LEFT, padx=2)

    def _on_load(self) -> None:
        self.on_load()

    def _on_save(self) -> None:
        self.on_save()

    def _on_save_as(self) -> None:
        self.on_save_as()

    def get_selected_template(self) -> str:
        return self.cmb_template.get()


class ModelSelectRow(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.on_select: Callable[[str], None] = lambda p: None

        ttk.Label(self, text="模型:").pack(side=tk.LEFT, padx=(0, 5))

        self.btn_browse = ttk.Button(self, text="浏览", command=self._on_click)
        self.btn_browse.pack(side=tk.LEFT, padx=(0, 5))

        self.lbl_model = ttk.Label(self, text="未选择", width=30)
        self.lbl_model.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _on_click(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="选择模型文件",
            filetypes=[("GGUF 模型", "*.gguf"), ("所有文件", "*")],
        )
        if path:
            self.on_select(path)

    def set_model(self, path: str) -> None:
        display = path
        if len(display) > 40:
            display = "..." + display[-37:]
        self.lbl_model.config(text=display)


class ParamTable(ttk.Frame):
    COLUMNS = ("name", "value", "action")

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.tree = ttk.Treeview(
            self,
            columns=self.COLUMNS,
            show="headings",
            height=8,
        )

        self.tree.heading("name", text="参数名")
        self.tree.heading("value", text="值")
        self.tree.heading("action", text="操作")

        self.tree.column("name", width=100, minwidth=60)
        self.tree.column("value", width=200, minwidth=100)
        self.tree.column("action", width=60, minwidth=50)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._params: list[Parameter] = []

        self.tree.bind("<Double-1>", self._on_double_click)

    def clear(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        self._params.clear()

    def insert_param(self, param: Parameter) -> None:
        self.tree.insert(
            "", "end",
            values=(param.name, param.value or "", "删除"),
        )
        self._params.append(param)

    def _on_double_click(self, event: tk.Event) -> None:
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id or not column:
            return

        col_idx = int(column.replace("#", "")) - 1
        if col_idx < 0 or col_idx >= len(self.COLUMNS):
            return

        col_name = self.COLUMNS[col_idx]
        values = list(self.tree.item(item_id, "values"))

        if col_name == "action":
            self._on_delete(item_id)
        else:
            self._edit_text(item_id, values, col_idx, col_name)

    def _edit_text(
        self, item_id: str, values: list[str], col_idx: int, col_name: str
    ) -> None:
        bbox = self.tree.bbox(item_id, self.COLUMNS[col_idx])
        if not bbox:
            return
        x, y, w, h = bbox

        entry = ttk.Entry(self.tree, width=w // 7)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()

        def on_confirm(event: object = None) -> None:
            new_val = entry.get()
            values[col_idx] = new_val
            self.tree.item(item_id, values=tuple(values))
            entry.destroy()
            self._sync_item_to_params(item_id)

        entry.bind("<Return>", on_confirm)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.bind("<FocusOut>", on_confirm)

    def _sync_item_to_params(self, item_id: str) -> None:
        idx = self._get_item_index(item_id)
        if idx is None:
            return
        values = self.tree.item(item_id, "values")
        self._params[idx] = Parameter(
            name=str(values[0]),
            value=str(values[1]) if values[1] else None,
            category="other",
            required=False,
        )

    def _get_item_index(self, item_id: str) -> int | None:
        children = list(self.tree.get_children())
        try:
            return children.index(item_id)
        except ValueError:
            return None

    def _on_delete(self, item_id: str) -> None:
        idx = self._get_item_index(item_id)
        if idx is not None:
            self._params.pop(idx)
        self.tree.delete(item_id)

    def get_parameters(self) -> list[Parameter]:
        result: list[Parameter] = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            result.append(
                Parameter(
                    name=str(values[0]),
                    value=str(values[1]) if values[1] else None,
                    category="other",
                    required=False,
                )
            )
        return result


class CmdPreviewRow(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.on_copy: Callable[[], None] = lambda: None
        self._full_cmd: str = ""

        ttk.Label(self, text="预览:").grid(row=0, column=0, sticky=tk.NW, padx=(0, 5))

        self.lbl_cmd_preview = ttk.Label(
            self, text="", foreground="#333", wraplength=600,
        )
        self.lbl_cmd_preview.grid(row=0, column=1, sticky=tk.W, padx=5)

        self.btn_copy_cmd = ttk.Button(
            self, text="复制", command=self._on_copy, width=6
        )
        self.btn_copy_cmd.grid(row=0, column=2, sticky=tk.E, padx=5)

    def _on_copy(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self._full_cmd)
        self.btn_copy_cmd.config(text="已复制")
        self.after(1500, lambda: self.btn_copy_cmd.config(text="复制"))

    def set_preview(self, cmd: str) -> None:
        self._full_cmd = cmd
        self.lbl_cmd_preview.config(text=cmd)

    def get_preview(self) -> str:
        return self._full_cmd

    def show_copied(self) -> None:
        original = self.btn_copy_cmd.cget("text")
        self.btn_copy_cmd.config(text="已复制")
        self.after(1500, lambda: self.btn_copy_cmd.config(text=original))
