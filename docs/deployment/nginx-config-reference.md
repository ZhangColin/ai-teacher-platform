# Nginx 配置参考

本文件提供了项目的 Nginx 配置示例，供部署时参考。

## 标准配置（HTTP）

此配置适用于直接部署，添加到服务器的 Nginx 配置中。

```nginx
# ============================================
# AI 教育平台 - studio.aieducenter.com
# ============================================
server {
    listen 80;
    server_name studio.aieducenter.com;

    # 前端静态文件
    location / {
        root /home/studio/frontend-dist;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由支持
        
        # 静态资源缓存
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 流式输出支持（AI 对话需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        
        # 超时设置（AI 请求可能较长）
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态文件（用户上传的 HTML 工具、作品）
    location /static {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 日志
    access_log /var/log/nginx/studio_access.log;
    error_log /var/log/nginx/studio_error.log;
}
```

## HTTPS 配置（生产环境推荐）

配置 SSL 证书后使用此配置。

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name studio.aieducenter.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name studio.aieducenter.com;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 前端静态文件
    location / {
        root /home/studio/frontend-dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 流式输出支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态文件
    location /static {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 日志
    access_log /var/log/nginx/studio_access.log;
    error_log /var/log/nginx/studio_error.log;
}
```

## 配置说明

### 关键配置项

1. **前端路由支持**
   ```nginx
   try_files $uri $uri/ /index.html;
   ```
   用于支持 Vue Router 的 history 模式。

2. **流式输出支持**
   ```nginx
   proxy_http_version 1.1;
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection "upgrade";
   proxy_buffering off;
   ```
   AI 对话功能需要流式输出，必须禁用缓冲。

3. **超时设置**
   ```nginx
   proxy_read_timeout 300s;
   ```
   AI 请求可能需要较长时间，需要设置较大的超时时间。

4. **静态资源缓存**
   ```nginx
   expires 30d;
   add_header Cache-Control "public, immutable";
   ```
   提高前端资源加载速度。

### 添加配置的方法

#### 方法1: 创建独立配置文件（推荐）

```bash
# 在服务器上执行
vim /home/data/nginx/conf.d/studio.conf

# 粘贴上面的配置，保存
# 测试并重载
podman exec <nginx-container> nginx -t
podman exec <nginx-container> nginx -s reload
```

#### 方法2: 添加到现有配置文件

```bash
# 编辑现有配置
vim /home/data/nginx/conf.d/default.conf

# 在文件末尾添加配置
# 测试并重载
podman exec <nginx-container> nginx -t
podman exec <nginx-container> nginx -s reload
```

### 验证配置

```bash
# 测试配置语法
podman exec <nginx-container> nginx -t

# 查看 Nginx 日志
podman exec <nginx-container> tail -f /var/log/nginx/studio_error.log

# 测试前端访问
curl -I http://studio.aieducenter.com

# 测试 API 访问
curl http://studio.aieducenter.com/api/v1/navigation
```

## 常见问题

### 1. 502 Bad Gateway

**原因**: 后端服务未启动或端口配置错误

**解决**:
```bash
# 检查后端服务
sudo systemctl status studio-backend

# 测试后端端口
curl http://localhost:8000/api/v1/navigation
```

### 2. 前端 404 错误

**原因**: 前端文件路径配置错误

**解决**:
```bash
# 检查前端文件是否存在
ls -la /home/studio/frontend-dist/

# 检查 Nginx 配置中的 root 路径
cat /home/data/nginx/conf.d/studio.conf | grep root
```

### 3. API 请求超时

**原因**: 超时设置过短

**解决**:
```nginx
# 增加超时时间
proxy_read_timeout 600s;  # 增加到 10 分钟
```

### 4. 静态资源 404

**原因**: `/static` 路径配置错误

**解决**:
```nginx
# 确保代理到后端
location /static {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
}
```

## 性能优化

### 1. 启用 Gzip 压缩

在主配置文件（/etc/nginx/nginx.conf）中：

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript 
           application/json application/javascript application/xml+rss;
```

### 2. 增加客户端上传限制

```nginx
server {
    client_max_body_size 100M;  # 允许上传 100MB 的文件
    # ...
}
```

### 3. 启用 HTTP/2

```nginx
server {
    listen 443 ssl http2;  # 启用 HTTP/2
    # ...
}
```

---

**文档版本**: v1.0  
**最后更新**: 2026-01-11

