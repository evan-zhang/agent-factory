# Doc Viewer 部署指南

## 架构

```
用户 → http://doc.20100706.xyz:80 → Nginx 反代 → 127.0.0.1:8080 → FastAPI (app.py)
```

## 首次部署

```bash
# 1. 创建目录
mkdir -p /data/doc-viewer/data

# 2. 安装 python3-venv
apt-get update && apt-get install -y python3-venv

# 3. 创建虚拟环境
python3 -m venv /data/doc-viewer/venv

# 4. 安装依赖（需要外网访问，可能需配置代理）
/data/doc-viewer/venv/bin/pip install --no-cache-dir fastapi uvicorn "python-multipart>=0.0.6" markdown

# 5. 上传 app.py 到 /data/doc-viewer/app.py

# 6. 配置 systemd service
cat > /etc/systemd/system/doc-viewer.service << 'EOF'
[Unit]
Description=Doc Viewer - Markdown/HTML Upload and Preview Service
After=network.target

[Service]
Type=simple
User=root
Environment=DOC_HOST=<域名>
Environment=DOC_PORT=8080
Environment=DOC_PUBLIC_PORT=80
Environment=DOC_DATA_DIR=/data/doc-viewer/data
Environment=DOC_RETENTION_DAYS=30
ExecStart=/data/doc-viewer/venv/bin/python /data/doc-viewer/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. 启动服务
systemctl daemon-reload
systemctl enable doc-viewer
systemctl start doc-viewer

# 8. Nginx 反代配置
cat > /etc/nginx/sites-enabled/doc.<domain>.xyz << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name doc.<domain>.xyz;
    client_max_body_size 15m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

nginx -t && nginx -s reload

# 9. 开放防火墙（如果用 ufw）
ufw allow 80/tcp
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DOC_HOST | doc.20100706.xyz | 对外域名，用于生成 URL |
| DOC_PORT | 8080 | 监听端口 |
| DOC_PUBLIC_PORT | 0 | 对外端口（0=自动，80 则省略端口号） |
| DOC_DATA_DIR | /data/doc-viewer/data | 数据存储目录 |
| DOC_RETENTION_DAYS | 30 | 文件保留天数 |

## 依赖版本（已验证）

- Python 3.9+ / 3.11+
- fastapi >= 0.128
- uvicorn >= 0.39
- python-multipart >= 0.0.20
- markdown >= 3.9
