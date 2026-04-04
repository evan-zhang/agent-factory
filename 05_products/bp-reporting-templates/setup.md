# bp-reporting-templates 安装配置

## 环境变量

| 变量名 | 说明 | 必须 |
|--------|------|------|
| `BP_APP_KEY` | BP 系统 AppKey，从 BP 后台→开放平台获取 | ✅ |
| `COMPANY_APP_KEY` | 备用企业 AppKey（fallback）| ❌ |

```bash
export BP_APP_KEY='your_app_key_here'
```

## External Endpoints

| 地址 | 用途 |
|------|------|
| BP 系统 API（内网）| 拉取绩效周期、组织、KPI 数据 |

## 依赖安装

```bash
pip install -r requirements.txt
```
