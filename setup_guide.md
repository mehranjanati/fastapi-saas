# راهنمای راه‌اندازی کامل FastAPI و n8n با Hasura

## پیش‌نیازها

قبل از شروع، مطمئن شوید که موارد زیر را نصب کرده‌اید:
- Python 3.9+ 
- Node.js 14+ (برای n8n)
- Redis
- دسترسی به یک نمونه از Hasura (نسخه Cloud یا خودمیزبان)
- دیتابیس (مانند Neon PostgreSQL یا CockroachDB)

## مرحله 1: راه‌اندازی FastAPI

1. **نصب وابستگی‌ها**:
   ```bash
   cd fastapi_project
   pip install -r requirements.txt
   ```

2. **تنظیم متغیرهای محیطی**:
   ایجاد یک فایل `.env` در دایرکتوری `fastapi_project` با محتوای زیر:
   ```
   HASURA_ENDPOINT=https://your-hasura-endpoint/v1/graphql
   HASURA_ADMIN_SECRET=your-hasura-admin-secret
   JWT_SECRET=your-jwt-secret
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```

3. **اجرای سرور FastAPI**:
   ```bash
   uvicorn main:app --reload
   ```

4. **بررسی اجرا**:
   به آدرس `http://localhost:8000/docs` مراجعه کنید تا مستندات Swagger API را مشاهده کنید.

## مرحله 2: راه‌اندازی n8n

1. **نصب n8n**:
   ```bash
   npm install -g n8n@1.0.0
   ```

2. **اجرای n8n**:
   ```bash
   n8n start --tunnel
   ```

3. **وارد کردن workflow نمونه**:
   - به رابط کاربری وب n8n در آدرس `http://localhost:5678` مراجعه کنید.
   - روی دکمه Workflows کلیک کنید و سپس "Import from File" را انتخاب کنید.
   - فایل `n8n_setup/order_processing_workflow.json` را انتخاب کنید.

4. **فعال‌سازی workflow**:
   - workflow وارد شده را باز کنید.
   - روی دکمه "Activate" کلیک کنید تا webhook فعال شود.
   - آدرس webhook را کپی کنید (چیزی شبیه `https://xxx.hooks.n8n.cloud/webhook/process-order`).

## مرحله 3: تنظیم Hasura

1. **ایجاد جدول orders**:
   در کنسول Hasura، SQL زیر را اجرا کنید:
   ```sql
   CREATE TABLE orders (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id TEXT NOT NULL,
     status TEXT NOT NULL DEFAULT 'pending',
     details JSONB,
     processing_result JSONB,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   CREATE INDEX idx_orders_user_id ON orders(user_id);
   CREATE INDEX idx_orders_status ON orders(status);
   ```

2. **تنظیم Event Trigger**:
   - در بخش Events کنسول Hasura، یک trigger جدید ایجاد کنید.
   - نام: `order_created_trigger`
   - جدول: `orders`
   - عملیات: `insert`
   - آدرس webhook: آدرس کپی‌شده از n8n را اینجا وارد کنید.
   - در بخش Headers، دو هدر زیر را اضافه کنید:
     - `x-hasura-endpoint`: آدرس GraphQL endpoint هاسورا
     - `x-hasura-admin-secret`: کلید ادمین هاسورا

3. **تنظیم قوانین دسترسی مبتنی بر نقش**:
   - به بخش Permissions در جدول orders بروید.
   - برای نقش `user`:
     - Insert: `{"user_id":{"_eq":"X-Hasura-User-Id"}}`
     - Select: `{"user_id":{"_eq":"X-Hasura-User-Id"}}`
     - Update: `{"user_id":{"_eq":"X-Hasura-User-Id"},"status":{"_nin":["processed"]}}`
     - Delete: `{"user_id":{"_eq":"X-Hasura-User-Id"},"status":{"_eq":"pending"}}`
   - برای نقش `admin`:
     - همه دسترسی‌ها بدون محدودیت

## مرحله 4: تست سیستم

1. **دریافت توکن احراز هویت**:
   ```bash
   curl -X POST http://localhost:8000/token -d "username=admin&password=password"
   ```

2. **ایجاد یک سفارش**:
   ```bash
   curl -X POST http://localhost:8000/api/create-order \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"details":{"product_id":"123","quantity":1}}'
   ```

3. **بررسی وضعیت سفارش**:
   ```bash
   curl -X GET http://localhost:8000/api/orders \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **بررسی workflow در n8n**:
   - به n8n dashboard مراجعه کنید.
   - در بخش Executions، باید یک اجرای موفق از workflow را مشاهده کنید.
   - جزئیات اجرا را بررسی کنید تا مطمئن شوید که پردازش سفارش به درستی انجام شده است.

## نکات مهم

1. **امنیت**:
   - از HTTPS برای تمام ارتباطات استفاده کنید.
   - توکن JWT را در یک محل امن نگهداری کنید.
   - کلید ادمین Hasura را به اشتراک نگذارید.

2. **مقیاس‌پذیری**:
   - برای محیط‌های production، از چند نمونه FastAPI استفاده کنید.
   - Redis را برای caching تنظیم کنید.
   - از load balancer استفاده کنید.

3. **مانیتورینگ**:
   - از Prometheus برای جمع‌آوری متریک‌ها استفاده کنید.
   - از Grafana برای visualize کردن متریک‌ها استفاده کنید.
   - از Jaeger برای tracing استفاده کنید.

4. **مستندسازی**:
   - تمام تغییرات API را مستند کنید.
   - از Swagger UI برای مستندسازی API استفاده کنید.

این راهنما یک پایه اولیه برای راه‌اندازی سیستم فراهم می‌کند. برای استفاده در محیط production، ممکن است نیاز به تنظیمات اضافی و بهینه‌سازی‌ها داشته باشید. 