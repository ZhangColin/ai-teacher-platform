# AI 服务配置说明

## 环境变量配置

在 `.env` 文件中配置以下环境变量：

### 必需配置

```bash
# 当前使用的AI服务提供商（kimi 或 deepseek）
CURRENT_PROVIDER=kimi

# Kimi API配置
KIMI_API_KEY=sk-your-api-key-here
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k

# DeepSeek API配置（可选）
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 可选配置

```bash
# AI请求超时时间（秒），默认120秒
# 如果网络较慢或使用代理，可以适当增加此值
AI_REQUEST_TIMEOUT=120

# HTTP/HTTPS代理设置（如果需要）
# 注意：代理可能导致SSL握手超时，建议根据实际情况调整超时时间
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=https://proxy.example.com:8080
```

## 常见问题

### 1. 请求超时 (Request timed out)

**症状：**
```
openai.APITimeoutError: Request timed out
httpcore.ConnectTimeout: The handshake operation timed out
```

**可能原因：**
- 网络连接不稳定
- 使用代理导致连接延迟
- AI服务提供商响应慢
- 超时时间设置太短

**解决方案：**
1. 检查网络连接是否正常
2. 如果使用代理，确认代理配置正确
3. 在 `.env` 中增加超时时间：
   ```bash
   AI_REQUEST_TIMEOUT=180  # 增加到180秒
   ```
4. 如果不需要代理，移除代理配置：
   ```bash
   # HTTP_PROXY=...
   # HTTPS_PROXY=...
   ```

### 2. SSL握手超时

**症状：**
```
_ssl.c:989: The handshake operation timed out
```

**可能原因：**
- 网络防火墙阻止了SSL连接
- 代理服务器配置问题
- DNS解析慢

**解决方案：**
1. 测试网络连接：
   ```bash
   curl -v https://api.moonshot.cn/v1
   ```
2. 如果使用代理，检查代理是否支持HTTPS
3. 尝试不使用代理直接连接
4. 增加超时时间

### 3. 连接被拒绝 (Connection refused)

**可能原因：**
- API密钥错误或已过期
- Base URL配置错误
- AI服务提供商服务异常

**解决方案：**
1. 检查 API Key 是否正确（必须以 `sk-` 开头）
2. 检查 Base URL 是否正确
3. 访问AI服务提供商官网确认服务状态

## 性能优化建议

1. **合理设置超时时间：**
   - 生产环境：120-180秒
   - 开发环境：60-120秒
   - 测试环境：30-60秒

2. **网络优化：**
   - 使用稳定的网络连接
   - 如非必要，避免使用代理
   - 考虑使用国内AI服务商（如Kimi、DeepSeek）以减少延迟

3. **监控和日志：**
   - 定期检查日志中的超时错误
   - 监控AI服务的响应时间
   - 根据实际情况调整超时配置

## 测试配置

测试AI服务配置是否正确：

```bash
cd backend
python -c "from src.services.ai_service import AIService; import asyncio; print(asyncio.run(AIService().generate_welcome_message('你是一个AI助手')))"
```

如果配置正确，应该返回AI生成的欢迎消息。
