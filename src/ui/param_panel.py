from __future__ import annotations

import tkinter
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable

from src.models.server_config import LaunchConfig, Parameter
from src.services.config_service import ConfigService
from src.services.param_service import ParamService
from src.utils.file_utils import normalize_path


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

        on_file_selected: Callable[[str], None] = lambda p: None
        on_history_selected: Callable[[str], None] = lambda p: None
        on_load_template: Callable[[str], None] = lambda n: None
        on_save_template: Callable[[str], None] = lambda n: None
        on_save_as_template: Callable[[], None] = lambda: None
        on_parameter_changed: Callable[[list[Parameter]], None] = lambda p: None

        self._on_file_selected = on_file_selected
        self._on_history_selected = on_history_selected
        self._on_load_template = on_load_template
        self._on_save_template = on_save_template
        self._on_save_as_template = on_save_as_template
        self._on_parameter_changed = on_parameter_changed

        self._build_ui()

    def _build_ui(self) -> None:
        self._file_row = FileSelectRow(self)
        self._template_row = TemplateRow(self)
        self._param_table = ParamTable(self)
        self._cmd_preview = CmdPreviewRow(self)

        add_btn = ttk.Button(self, text="+ 添加参数", command=self._on_add_parameter)

        self._file_row.pack(fill=tk.X, padx=5, pady=(5, 0))
        self._template_row.pack(fill=tk.X, padx=5, pady=5)
        self._param_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        add_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        self._cmd_preview.pack(fill=tk.X, padx=5, pady=(0, 5))

        self._file_row.on_select_file = self._on_select_file
        self._file_row.on_history_change = self._on_history_change
        self._template_row.on_load = self._on_load_template_clicked
        self._template_row.on_save = self._on_save_template_clicked
        self._template_row.on_save_as = self._on_save_as_template_clicked
        self._cmd_preview.on_copy = self._on_copy_command

    # -- FileSelectRow callbacks --

    def _on_select_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Select Server Executable",
            filetypes=[("Server Binary", "server")],
        )
        if not path:
            return
        path = normalize_path(path)
        self._server_path = path
        self._file_row.set_path(path)
        self._on_file_selected(path)

    def _on_history_change(self, path: str) -> None:
        self._server_path = path
        self._file_row.set_path(path)
        self._on_history_selected(path)

    # -- TemplateRow callbacks --

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

    # -- ParamTable callbacks --

    def _on_add_parameter(self) -> None:
        param = Parameter(name="", value="", category="other", required=False)
        self._parameters.append(param)
        self._param_table.insert_param(param)
        self._on_parameter_changed(self._parameters)

    def _on_param_edited(self, idx: int, param: Parameter) -> None:
        self._parameters[idx] = param
        self.update_command_preview()
        self._on_parameter_changed(self._parameters)

    def _on_param_deleted(self, idx: int) -> None:
        self._parameters.pop(idx)
        self.update_command_preview()
        self._on_parameter_changed(self._parameters)

    # -- CmdPreviewRow callbacks --

    def _on_copy_command(self) -> None:
        cmd = self._cmd_preview.get_preview()
        self.clipboard_clear()
        self.clipboard_append(cmd)
        self._cmd_preview.show_copied()

    # -- Public API --

    def load_parameters(self, params: list[Parameter]) -> None:
        self._parameters = list(params)
        self._param_table.clear()
        for p in self._parameters:
            self._param_table.insert_param(p)
        self.update_command_preview()

    def get_current_params(self) -> list[Parameter]:
        return list(self._parameters)

    def get_launch_config(self) -> LaunchConfig:
        cmd = self._build_shell_command()
        return LaunchConfig(
            server_path=self._server_path,
            shell_command=cmd,
            parameters=list(self._parameters),
            selected_template=self._template_row.get_selected_template(),
        )

    def update_command_preview(self) -> None:
        config = LaunchConfig(
            server_path=self._server_path,
            shell_command="",
            parameters=list(self._parameters),
        )
        cmd = self._param_service.build_command(config)
        self._cmd_preview.set_preview(cmd)

    def _build_shell_command(self) -> str:
        config = LaunchConfig(
            server_path=self._server_path,
            shell_command="",
            parameters=list(self._parameters),
        )
        return self._param_service.build_command(config)

    def set_server_path(self, path: str) -> None:
        self._server_path = path
        self._file_row.set_path(path)

    def get_server_path(self) -> str:
        return self._server_path


class FileSelectRow(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.on_select_file: Callable[[], None] = lambda: None
        self.on_history_change: Callable[[str], None] = lambda p: None

        self.btn_select_file = ttk.Button(self, text="选择文件", command=self._on_click)
        self.lbl_server_path = ttk.Label(self, text="未选择", width=40)
        self.cmb_history = ttk.Combobox(self, state="readonly", width=40)

        self.btn_select_file.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_server_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cmb_history.pack(side=tk.RIGHT, padx=(5, 0))

        self.cmb_history.bind("<<ComboboxSelected>>", self._on_select)

    def _on_click(self) -> None:
        self.on_select_file()

    def _on_select(self, event: object) -> None:
        path = self.cmb_history.get()
        if path:
            self.on_history_change(path)

    def set_path(self, path: str) -> None:
        display = path
        if len(display) > 50:
            display = "..." + display[-47:]
        self.lbl_server_path.config(text=display)

    def set_history(self, paths: list[str]) -> None:
        self.cmb_history["values"] = paths


class TemplateRow(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.on_load: Callable[[], None] = lambda: None
        self.on_save: Callable[[], None] = lambda: None
        self.on_save_as: Callable[[], None] = lambda: None

        ttk.Label(self, text="模板:").pack(side=tk.LEFT, padx=(0, 2))

        templates = list(
            ParamService.PRESET_TEMPLATES.keys()
        )
        self.cmb_template = ttk.Combobox(
            self,
            values=templates,
            state="readonly",
            width=15,
        )
        self.cmb_template.pack(side=tk.LEFT, padx=(0, 5))
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


class ParamTable(ttk.Frame):
    COLUMNS = ("name", "value", "category", "required")
    CATEGORY_VALUES = ("model", "context", "gpu", "network", "other", "基础", "GPU", "性能", "网络")

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
        self.tree.heading("category", text="分类")
        self.tree.heading("required", text="必填")

        self.tree.column("name", width=100, minwidth=60)
        self.tree.column("value", width=200, minwidth=100)
        self.tree.column("category", width=80, minwidth=60)
        self.tree.column("required", width=50, minwidth=30)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._action_buttons: dict[str, ttk.Button] = {}
        self._params: list[Parameter] = []

        self.tree.bind("<Double-1>", self._on_double_click)

    def clear(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        self._action_buttons.clear()
        self._params.clear()

    def insert_param(self, param: Parameter) -> None:
        required_text = "\u2713" if param.required else ""
        item_id = self.tree.insert(
            "",
            "end",
            values=(param.name, param.value or "", param.category, required_text),
        )
        btn = ttk.Button(
            self,
            text="删除",
            width=6,
            command=lambda iid=item_id: self._on_delete(iid),
        )
        self._action_buttons[item_id] = btn
        self._params.append(param)
        self._position_action_buttons()

    def _position_action_buttons(self) -> None:
        canvas = self.tree.yview()
        for item_id, btn in self._action_buttons.items():
            try:
                bbox = self.tree.bbox(item_id, "name")
                if bbox:
                    x, y, w, h = bbox
                    btn.place(x=x + w + 5, y=y + (h - 20) // 2)
            except tk.TclError:
                btn.place_forget()

    def _on_double_click(self, event: tkinter.Event) -> None:
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id or not column:
            return

        col_idx = int(column.replace("#", "")) - 1
        if col_idx < 0 or col_idx >= len(self.COLUMNS):
            return

        col_name = self.COLUMNS[col_idx]
        values = list(self.tree.item(item_id, "values"))

        if col_name == "category":
            self._edit_category(item_id, values, col_idx)
        elif col_name == "required":
            self._edit_required(item_id, values, col_idx)
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

    def _edit_category(
        self, item_id: str, values: list[str], col_idx: int
    ) -> None:
        bbox = self.tree.bbox(item_id, "category")
        if not bbox:
            return
        x, y, w, h = bbox

        combo = ttk.Combobox(
            self.tree,
            values=self.CATEGORY_VALUES,
            state="readonly",
            width=w // 7,
        )
        combo.set(values[col_idx])
        combo.place(x=x, y=y, width=w, height=h)
        combo.focus_set()

        def on_confirm(event: object = None) -> None:
            values[col_idx] = combo.get()
            self.tree.item(item_id, values=tuple(values))
            combo.destroy()
            self._sync_item_to_params(item_id)

        combo.bind("<Return>", on_confirm)
        combo.bind("<FocusOut>", on_confirm)

    def _edit_required(
        self, item_id: str, values: list[str], col_idx: int
    ) -> None:
        values[col_idx] = "" if values[col_idx] else "\u2713"
        self.tree.item(item_id, values=tuple(values))
        self._sync_item_to_params(item_id)

    def _sync_item_to_params(self, item_id: str) -> None:
        idx = self._get_item_index(item_id)
        if idx is None:
            return
        values = self.tree.item(item_id, "values")
        self._params[idx] = Parameter(
            name=str(values[0]),
            value=str(values[1]) if values[1] else None,
            category=str(values[2]),
            required=bool(values[3]),
        )
        self._on_data_changed()

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
            self._on_data_changed()
        btn = self._action_buttons.pop(item_id, None)
        if btn:
            btn.destroy()
        self.tree.delete(item_id)

    def get_parameters(self) -> list[Parameter]:
        result: list[Parameter] = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            result.append(
                Parameter(
                    name=str(values[0]),
                    value=str(values[1]) if values[1] else None,
                    category=str(values[2]),
                    required=bool(values[3]),
                )
            )
        return result

    def _on_data_changed(self) -> None:
        pass


class CmdPreviewRow(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.on_copy: Callable[[], None] = lambda: None

        ttk.Label(self, text="预览:").pack(side=tk.LEFT, padx=(0, 5))

        self.lbl_cmd_preview = ttk.Label(
            self, text="", foreground="#333", wraplength=500
        )
        self.lbl_cmd_preview.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_copy_cmd = ttk.Button(
            self, text="复制", command=self._on_copy, width=6
        )
        self.btn_copy_cmd.pack(side=tk.RIGHT, padx=(5, 0))

    def _on_copy(self) -> None:
        self.on_copy()

    def set_preview(self, cmd: str) -> None:
        display = cmd
        if len(display) > 80:
            display = display[:77] + "..."
        self.lbl_cmd_preview.config(text=display)

    def get_preview(self) -> str:
        return self.lbl_cmd_preview.cget("text")

    def show_copied(self) -> None:
        original = self.btn_copy_cmd.cget("text")
        self.btn_copy_cmd.config(text="已复制")
        self.after(1500, lambda: self.btn_copy_cmd.config(text=original))
