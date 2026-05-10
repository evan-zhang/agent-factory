# AF-20260510-001 — Doc Viewer

## 定位
文档上传与预览 Web 服务。支持 Markdown / HTML / TXT 格式，上传后生成可访问的预览链接。

## 功能
- 文件上传（拖拽 / 选择文件 / 粘贴文本）
- 自动格式检测（Markdown / HTML / Text）
- 在线渲染预览（Markdown → HTML、HTML 直接展示）
- 按天分组的文档列表首页
- 原始文件下载、API 元信息查询
- 30 天自动过期（可配置）

## 技术栈
- Python 3 + FastAPI
- systemd 部署
- 域名：doc.20100706.xyz

## 目录结构
```
doc-viewer/
  app.py              — 主应用（FastAPI）
  doc-viewer.service  — systemd 服务配置
```

## 状态
- 已上线运行
