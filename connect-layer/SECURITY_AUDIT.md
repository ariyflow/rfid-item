# 安全审计报告

**项目:** RFID Connect Layer - 串口调试工具  
**审计日期:** 2026-03-13  
**审计范围:** main.py 代码安全审查

---

## 🔒 已修复的安全漏洞

### 1. HTML 注入漏洞 (高危)
**问题:** 日志输出直接使用用户数据渲染 HTML，可能导致 XSS 攻击  
**位置:** `_append_log()` 方法  
**修复:** 使用 `html.escape()` 对所有日志消息进行转义

```python
# 修复前
log_text = f"[{timestamp}] [{level}] {message}\n"

# 修复后
safe_message = html.escape(message)
log_text = f"[{timestamp}] [{level}] {safe_message}\n"
```

### 2. 文件路径遍历漏洞 (高危)
**问题:** 导出日志时未验证文件路径，可能写入系统关键目录  
**位置:** `_export_log()` 方法  
**修复:** 
- 添加文件扩展名白名单检查
- 验证写入路径是否在用户目录内
- 对危险扩展名进行拦截

```python
# 允许的扩展名
ALLOWED_LOG_EXTENSIONS = {'.txt', '.log', '.md'}

# 危险扩展名拦截
dangerous_exts = {'.exe', '.bat', '.cmd', '.sh', '.py', '.js', '.vbs'}
```

### 3. 缓冲区溢出风险 (中危)
**问题:** 无限制接收/发送数据，可能导致内存耗尽  
**位置:** `Logger.rx()`, `_send_data()`  
**修复:** 添加数据大小限制常量

```python
MAX_LOG_HISTORY = 10000      # 最大日志条数
MAX_DISPLAY_BYTES = 1048576  # 单次最大显示 1MB
MAX_SEND_BYTES = 65536       # 单次最大发送 64KB
```

### 4. 串口端口名称注入 (中危)
**问题:** 未验证串口端口名称格式，可能传入恶意路径  
**位置:** `SerialWorker.connect()`  
**修复:** 添加端口名称格式验证

```python
def _validate_port_name(self, port: str) -> bool:
    if not port or not isinstance(port, str):
        return False
    if not re.match(r'^[A-Za-z0-9/_\-\\.]+$', port):
        return False
    if len(port) > 256:
        return False
    return True
```

### 5. UI 文件路径遍历 (中危)
**问题:** 加载 UI 文件时未验证路径，可能加载恶意 UI 文件  
**位置:** `_load_ui()` 方法  
**修复:** 验证 UI 文件路径是否在脚本目录内

```python
script_dir = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(script_dir, "test.ui")
real_path = os.path.realpath(ui_path)
if not real_path.startswith(script_dir):
    sys.exit(1)
```

### 6. 错误信息泄露 (低危)
**问题:** 异常处理可能泄露内部实现细节  
**位置:** 多处异常处理  
**修复:** 简化错误消息，不泄露堆栈信息

### 7. 日志历史内存溢出 (低危)
**问题:** 日志历史无限制增长，可能导致内存耗尽  
**位置:** `Logger._emit_log()`  
**修复:** 添加最大历史条数限制并自动截断

```python
if len(self._log_history) > self._max_history:
    self._log_history = self._log_history[-self._max_history:]
```

### 8. 端口描述 HTML 注入 (低危)
**问题:** 串口描述直接显示，可能包含恶意 HTML  
**位置:** `_refresh_ports()`  
**修复:** 对端口描述进行 HTML 转义

```python
safe_desc = html.escape(str(port.description))
```

---

## 📋 代码结构改进

### UI 加载方式变更
**原方式:** Python 代码硬编码创建所有 UI 控件  
**新方式:** 使用 `QtUiTools.QUiLoader` 从 `test.ui` 加载

**优点:**
- UI 设计与业务逻辑分离
- 可使用 Qt Designer 可视化编辑界面
- 代码更简洁，易于维护

```python
# 新增导入
from PySide6 import QtUiTools

# 加载 UI
loader = QtUiTools.QUiLoader()
ui_window = loader.load(ui_path, self)

# 绑定控件引用
self.comboPort = ui_window.findChild(QComboBox, "comboPort")
```

---

## ✅ 安全最佳实践建议

### 已实施
- [x] 输入验证（端口名称、HEX 数据、文件大小）
- [x] 输出编码（HTML 转义）
- [x] 资源限制（内存、数据大小）
- [x] 路径验证（UI 文件、导出文件）
- [x] 错误处理（不泄露敏感信息）

### 建议后续添加
- [ ] 添加串口通信速率限制（防止 Flood 攻击）
- [ ] 添加用户认证（如果部署为网络服务）
- [ ] 添加操作审计日志
- [ ] 对接收的二进制数据进行更严格的验证
- [ ] 添加配置文件签名验证

---

## 📁 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `main.py` | 重写 | 改用 UI 文件加载，修复所有安全漏洞 |
| `test.ui` | 更新 | 与 Python 代码 UI 结构完全匹配 |
| `SECURITY_AUDIT.md` | 新增 | 本安全审计报告 |

---

## 🧪 测试建议

1. **功能测试:**
   - 串口连接/断开
   - 数据发送/接收（文本和 HEX 模式）
   - 日志导出功能

2. **安全测试:**
   - 尝试发送超大文件（>64KB）
   - 尝试导出到系统目录
   - 尝试在发送数据中注入 HTML/脚本
   - 尝试修改 test.ui 添加恶意内容

3. **边界测试:**
   - 空数据发送
   - 非法 HEX 格式
   - 无效串口端口

---

**审计结论:** 已识别并修复 8 个安全问题，代码安全性显著提升。建议定期复审并添加建议的安全功能。
