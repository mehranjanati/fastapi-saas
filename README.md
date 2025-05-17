# Brandyto Backend

یک سیستم بک‌اند ترکیبی با استفاده از FastAPI و n8n برای توسعه سیستم‌های پیچیده و مقیاس‌پذیر.

## ویژگی‌ها

- توسعه سریع‌تر با استفاده از n8n
- انعطاف‌پذیری بیشتر در توسعه
- مقیاس‌پذیری بهتر
- نگهداری آسان‌تر

## ساختار پروژه

```
.
├── backend/           # کد بک‌اند
│   ├── api/          # کد FastAPI
│   └── tests/        # تست‌ها
├── docs/             # مستندات
│   ├── api/          # مستندات API
│   ├── architecture/ # مستندات معماری
│   ├── development/  # مستندات توسعه
│   └── workflows/    # مستندات n8n
└── n8n/              # کد n8n
```

## پیش‌نیازها

- Python 3.11+
- Node.js 18+
- Docker
- Redis

## نصب و راه‌اندازی

### 1. نصب وابستگی‌های Python

```bash
cd backend
pip install -r requirements.txt
```

### 2. نصب وابستگی‌های n8n

```bash
cd n8n
npm install
```

### 3. راه‌اندازی FastAPI

```bash
cd backend
uvicorn api.main:app --reload
```

### 4. راه‌اندازی n8n

```bash
cd n8n
n8n start
```

## مستندات

- [مستندات API](docs/api/endpoints.md)
- [مستندات n8n](docs/workflows/n8n.md)
- [مستندات معماری](docs/architecture/system.md)
- [چک‌لیست توسعه](docs/development/checklist.md)

## مشارکت

لطفاً قبل از مشارکت، [چک‌لیست توسعه](docs/development/checklist.md) را مطالعه کنید.

## لایسنس

MIT 