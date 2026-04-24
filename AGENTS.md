# llamacpp-panel

llama.cpp 轻量可视化管理工具，基于 Python Tkinter，无第三方 GUI 依赖。

## 技术栈

- 语言: Python 3.9+
- GUI: Tkinter (内置)
- 依赖: psutil

## 架构

```
src/
├── models/        # 数据模型 (@dataclass)
├── services/      # 业务逻辑
├── ui/            # Tkinter 界面
└── utils/         # 工具函数
```

## 编码规范

- 使用 `@dataclass` 定义数据类，完整类型标注
- 类: PascalCase | 函数/变量: snake_case | 常量: UPPER_SNAKE_CASE
- 导入顺序: 标准库 → 第三方 → 本地
- 模型不含业务逻辑，UI 仅调用 services

## 命名规范

- 文件: snake_case.py
- 测试: test_<module>.py

## Git Commit

```
<type>: <description>
```

| Type | 用途 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| refactor | 重构 |
| docs | 文档 |
| test | 测试 |
| chore | 构建/工具 |

## 测试

- 新功能需单元测试
- 测试结构镜像 src/

## 禁止事项

1. UI 直接访问数据层
2. 模型中包含业务逻辑
3. 提交前不跑测试
4. 硬编码配置值
5. 缺少类型标注
