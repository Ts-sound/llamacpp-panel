# llama.cpp Server 常用参数

参考：https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md

## 基础参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-m, --model` | 模型文件路径 | - |
| `-c, --ctx-size` | 上下文大小 (prompt context) | 0 (从模型读取) |
| `-n, --predict` | 最大预测 token 数 | -1 (无限) |
| `--port` | 服务监听端口 | 8080 |
| `--host` | 监听地址 (IP 或 UNIX socket) | 127.0.0.1 |
| `-hf, --hf-repo` | Hugging Face 模型仓库 (格式: user/model:quant) | - |
| `-a, --alias` | 模型别名 (用于 API 返回的 model id) | 模型路径 |
| `-h, --help` | 显示帮助信息 | - |
| `--version` | 显示版本和构建信息 | - |
| `--api-key` | API 认证密钥 (可多个，逗号分隔) | 无 |
| `--api-key-file` | API 密钥文件路径 | 无 |

## GPU 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-ngl, --gpu-layers` | 加载到 GPU 的层数 (可设为 'auto' 或 'all') | auto |
| `-dev, --device` | GPU 设备列表 (逗号分隔，如 `0,1`) | none (不 offload) |
| `--list-devices` | 列出可用设备并退出 | - |
| `-ts, --tensor-split` | 多 GPU 时模型分配比例 (如 `3,1`) | - |
| `-mg, --main-gpu` | 主 GPU 索引 (split-mode=none 或 row 时使用) | 0 |
| `-sm, --split-mode` | 多 GPU 分割模式: none/layer/row | layer |
| `-fit, --fit` | 自动调整参数以适应设备内存 | on |
| `-fitt, --fit-target` | 每个 GPU 的目标预留内存 (MiB) | 1024 |
| `-cmoe, --cpu-moe` | 将 MoE 权重保持在 CPU | - |
| `-kvo, --kv-offload` | 启用 KV cache offload | enabled |

## 采样参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--temp, --temperature` | 采样温度 (控制随机性) | 0.80 |
| `--top-k` | Top-K 采样 (保留前 K 个候选 token) | 40 (0=禁用) |
| `--top-p` | Top-P/Nucleus 采样 (累计概率阈值) | 0.95 (1.0=禁用) |
| `--min-p` | Min-P 采样 (相对于最高概率的最小概率) | 0.05 (0.0=禁用) |
| `--repeat-penalty` | 重复惩罚系数 | 1.00 (1.0=禁用) |
| `--repeat-last-n` | 用于重复惩罚的最后 N 个 token | 64 (0=禁用，-1=ctx_size) |
| `--presence-penalty` | 存在惩罚 (alpha presence) | 0.00 |
| `--frequency-penalty` | 频率惩罚 (alpha frequency) | 0.00 |
| `--dry-multiplier` | DRY (Don't Repeat Yourself) 惩罚倍数 | 0.00 |
| `--mirostat` | Mirostat 采样 (0=禁用，1/2=Mirostat 1.0/2.0) | 0 |
| `--mirostat-lr` | Mirostat 学习率 | 0.10 |
| `--mirostat-ent` | Mirostat 目标熵 | 5.00 |
| `--typical, --typical-p` | Locally typical 采样参数 p | 1.00 (禁用) |
| `-s, --seed` | RNG 随机种子 | -1 (随机) |
| `--ignore-eos` | 忽略 EOS token 继续生成 | false |

## 性能参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --threads` | 生成阶段 CPU 线程数 | -1 (自动) |
| `-tb, --threads-batch` | 批处理和 prompt 处理线程数 | 同 --threads |
| `-b, --batch-size` | 逻辑最大批处理大小 | 2048 |
| `-ub, --ubatch-size` | 物理最大批处理大小 | 512 |
| `-fa, --flash-attn` | Flash Attention (on/off/auto) | auto |
| `-np, --parallel` | 服务 slots 数量 (并发处理数) | -1 (自动) |
| `-cb, --cont-batching` | 启用连续批处理 | enabled |
| `-ctk, --cache-type-k` | KV cache K 的数据类型 (f32/f16/q8_0 等) | f16 |
| `-ctv, --cache-type-v` | KV cache V 的数据类型 | f16 |
| `--mlock` | 锁定模型在 RAM 中防止交换 | - |
| `--mmap` | 使用内存映射加载模型 | enabled |
| `--perf` | 启用内部性能计时 | false |

## 高级参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--lora` | LoRA 适配器路径 (可多个逗号分隔) | - |
| `--lora-scaled` | 带自定义缩放的 LoRA (格式: FNAME:SCALE) | - |
| `--grammar` | BNF-like 语法约束生成 | - |
| `--grammar-file` | 语法文件路径 | - |
| `-j, --json-schema` | JSON schema 约束生成 | - |
| `--draft, --draft-max` | 推测解码的 draft token 数 | 16 |
| `-md, --model-draft` | 推测解码的 draft 模型路径 | - |
| `-ngld, --gpu-layers-draft` | draft 模型的 GPU 层数 | auto |
| `--spec-type` | 无 draft 模型时的推测类型 | none |
| `-mm, --mmproj` | 多模态 projector 文件路径 | - |
| `--chat-template` | 自定义 Jinja chat 模板 | 从模型读取 |
| `--embedding` | 仅支持 embedding 用例 | disabled |
| `--rerank` | 启用 reranking 端点 | disabled |
| `--metrics` | 启用 Prometheus metrics 端点 | disabled |
| `-to, --timeout` | 服务读写超时 (秒) | 600 |
| `--ssl-key-file` | SSL 私钥文件 (PEM) | - |
| `--ssl-cert-file` | SSL 证书文件 (PEM) | - |

## 常用场景示例

### 基础启动
```bash
llama-server -m models/llama-3.Q4_K_M.gguf -c 4096 --port 8080
```

### GPU 加速
```bash
llama-server -m model.gguf -ngl 99 -c 8192 --host 0.0.0.0
```

### 多 GPU
```bash
llama-server -m model.gguf -ngl all -dev 0,1 -ts 3,1
```

### 推测解码
```bash
llama-server -m main.gguf -md draft.gguf -draft 16 -ngl 99 -ngld 99
```

### LoRA 适配
```bash
llama-server -m base.gguf --lora adapter1.gguf --lora-scaled adapter2.gguf:0.5
```

### JSON 输出约束
```bash
llama-server -m model.gguf -j '{"type": "object", "properties": {"name": {"type": "string"}}}'
```

### API 认证
```bash
llama-server -m model.gguf --api-key secret123 --port 8080
```

### 监控端点
```bash
llama-server -m model.gguf --metrics --slots --port 8080
```