# 故障排查指南

## SSH 端口映射

### 问题：远程端口转发失败

**症状：**
- SSH 连接成功但远程无法访问端口
- 错误：`Warning: remote port forwarding failed for listen port`

**原因：**
远程 SSH 服务器的 `GatewayPorts` 未启用，端口转发只能绑定到 localhost。

**解决方案：**

在远程 SSH 服务器上修改 sshd 配置：

```bash
# 编辑配置文件
sudo vim /etc/ssh/sshd_config

# 添加或修改以下配置：
GatewayPorts yes           # 允许远程端口转发绑定到所有接口
AllowTcpForwarding yes     # 允许 TCP 转发（默认启用）

# 重启 sshd 服务
sudo systemctl restart sshd
```

**验证：**
```bash
# 检查配置生效
sudo sshd -T | grep -E "gatewayports|allowtcpforwarding"

# 预期输出：
gatewayports yes
allowtcpforwarding yes
```

### 问题：SSH 连接超时

**症状：**
- 连接长时间无响应
- 错误：`Connection timed out`

**排查步骤：**

1. **检查网络连通性**
   ```bash
   ping 172.18.122.71
   ```

2. **检查 SSH 端口是否开放**
   ```bash
   nc -zv 172.18.122.71 22
   ```

3. **检查防火墙规则**
   ```bash
   # 远程服务器上
   sudo iptables -L -n | grep 22
   sudo firewall-cmd --list-ports  # CentOS/RHEL
   ```

4. **检查 sshd 服务状态**
   ```bash
   # 远程服务器上
   sudo systemctl status sshd
   ```

### 问题：SSH 密钥认证失败

**症状：**
- 错误：`Permission denied (publickey)`
- 密钥文件已指定但仍要求密码

**排查步骤：**

1. **检查密钥文件权限**
   ```bash
   # 本地
   chmod 600 ~/.ssh/id_rsa
   chmod 700 ~/.ssh
   ```

2. **检查远程 authorized_keys**
   ```bash
   # 远程服务器上
   cat ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

3. **测试密钥连接**
   ```bash
   ssh -i ~/.ssh/id_rsa -v username@172.18.122.71
   ```

### 问题：端口已被占用

**症状：**
- 错误：`bind: Address already in use`
- 远程端口已被其他服务占用

**排查步骤：**

1. **检查远程端口占用**
   ```bash
   # 远程服务器上
   sudo netstat -tlnp | grep :8081
   sudo lsof -i :8081
   ```

2. **解决方案**
   - 更换远程端口
   - 或停止占用端口的服务

## llama.cpp 进程

### 问题：进程启动失败

**症状：**
- 点击启动后无反应
- 日志显示错误

**排查步骤：**

1. **检查可执行文件路径**
   - 文件是否存在
   - 是否有执行权限
   ```bash
   ls -la /path/to/llama-server
   chmod +x /path/to/llama-server
   ```

2. **检查模型文件**
   ```bash
   ls -la /path/to/model.gguf
   ```

3. **检查参数配置**
   - `-m` 模型路径是否正确
   - `-c` 上下文大小是否合理
   - `-ngl` GPU 层数是否超出显卡容量

4. **手动测试**
   ```bash
   # 手动运行命令验证
   /path/to/llama-server -m model.gguf -c 2048 --port 8080
   ```

### 问题：进程意外退出

**症状：**
- 进程运行一段时间后消失
- 自动重启触发

**排查步骤：**

1. **检查内存使用**
   - 是否触发内存阈值重启
   - 查看监控面板的内存曲线

2. **检查 GPU 内存**
   ```bash
   nvidia-smi
   ```
   - 是否 OOM (Out of Memory)

3. **查看进程日志**
   - 检查 LogPanel 输出
   - 查看 `log/YYYY-MM-DD.txt` 文件

4. **调整参数**
   - 减少 `-c` 上下文大小
   - 减少 `-ngl` GPU 层数
   - 增加 `-b` batch size

### 问题：GPU 未被使用

**症状：**
- 进程运行但 GPU 内存未增长
- 推理速度慢

**排查步骤：**

1. **检查 GPU 驱动**
   ```bash
   nvidia-smi
   ```

2. **检查 CUDA 支持**
   ```bash
   llama-server --version | grep CUDA
   ```

3. **检查 `-ngl` 参数**
   - 是否设置为 0 或未设置
   - 建议设置为 `99` 或 `all`

4. **检查模型兼容性**
   - 某些模型可能不支持 GPU offload

## 性能问题

### 问题：推理速度慢

**排查步骤：**

1. **检查是否使用 GPU**
   ```bash
   nvidia-smi -l 1  # 实时监控 GPU 使用
   ```

2. **优化参数**
   ```bash
   # 增加 GPU 层数
   -ngl 99
   
   # 使用 Flash Attention
   -fa on
   
   # 增加批处理大小
   -b 2048 -ub 512
   
   # 减少上下文大小
   -c 4096  # 而不是 65536
   ```

3. **使用推测解码**
   ```bash
   # 配合小 draft 模型加速
   -md draft.gguf -draft 16
   ```

### 问题：内存占用高

**排查步骤：**

1. **减少上下文大小**
   ```bash
   -c 4096  # 根据需求调整
   ```

2. **使用量化 KV cache**
   ```bash
   -ctk q8_0 -ctv q8_0
   ```

3. **启用 KV offload**
   ```bash
   -kvo on  # 将 KV cache offload 到 CPU
   ```

## 配置问题

### 问题：配置加载失败

**症状：**
- 重启后配置未恢复
- 显示默认值

**排查步骤：**

1. **检查配置文件**
   ```bash
   cat config/app_config.json
   ```

2. **检查文件权限**
   ```bash
   ls -la config/
   chmod 644 config/app_config.json
   ```

3. **检查 JSON 格式**
   ```bash
   python -m json.tool config/app_config.json
   ```

4. **重建配置**
   - 删除损坏的配置文件
   - 重新保存配置

### 问题：模板加载失败

**排查步骤：**

1. **检查模板文件**
   ```bash
   ls -la config/templates/
   cat config/templates/min.json
   ```

2. **验证 JSON 格式**
   ```bash
   python -m json.tool config/templates/min.json
   ```