# Azure Deployment Guide - Mango Market Platform

## Overview
This guide provides steps to deploy the Mango Market Platform backend to **Azure App Service** for production.

---

## 📋 Prerequisites

1. **Azure Account**: Create one at https://azure.microsoft.com
2. **Azure CLI**: Install from https://docs.microsoft.com/cli/azure/install-azure-cli
3. **Git**: For pushing code to Azure
4. **Python 3.9+**: For local testing before deployment

---

## 🚀 Deployment Steps

### Step 1: Create Azure App Service

```bash
# Login to Azure
az login

# Create a resource group
az group create --name mango-market-rg --location eastus

# Create App Service Plan (Linux)
az appservice plan create \
  --name mango-market-plan \
  --resource-group mango-market-rg \
  --sku B2 \
  --is-linux

# Create Web App (Python 3.9)
az webapp create \
  --resource-group mango-market-rg \
  --plan mango-market-plan \
  --name mango-market-app \
  --runtime "PYTHON:3.9"
```

### Step 2: Configure Application Settings

Set environment variables in Azure Portal or via CLI:

```bash
az webapp config appsettings set \
  --resource-group mango-market-rg \
  --name mango-market-app \
  --settings \
    FLASK_ENV=production \
    DB_HOST=your-mysql-host.mysql.database.azure.com \
    DB_USER=your_user@your-server \
    DB_PASSWORD=your_strong_password \
    DB_NAME=mango_market_db \
    SMTP_SERVER=smtp.gmail.com \
    SMTP_PORT=465 \
    SMTP_EMAIL=your-email@gmail.com \
    SMTP_PASSWORD=your-app-password \
    SECRET_KEY=your-long-random-secret-key \
    ENCRYPTION_KEY=your-long-random-encryption-key \
    GUNICORN_WORKERS=4 \
    GUNICORN_TIMEOUT=120
```

### Step 3: Configure Startup Command

```bash
az webapp config set \
  --resource-group mango-market-rg \
  --name mango-market-app \
  --startup-file "gunicorn --workers 4 --worker-class sync --bind 0.0.0.0:8000 --timeout 120 --access-logfile - --error-logfile - app:app"
```

### Step 4: Deploy Code (Option A: Git)

```bash
# Initialize git repo (if not already done)
cd backend
git init
git add .
git commit -m "Initial commit"

# Get deployment URL
az webapp deployment source config-local-git \
  --resource-group mango-market-rg \
  --name mango-market-app

# Add Azure remote and push
git remote add azure <deployment-url>
git push azure main
```

### Step 5: Deploy Code (Option B: ZIP Upload)

```bash
# Create deployment package
cd backend
zip -r ../mango-market-backend.zip . -x ".git/*" ".venv/*" "__pycache__/*"

# Deploy using Azure CLI
az webapp deployment source config-zip \
  --resource-group mango-market-rg \
  --name mango-market-app \
  --src ../mango-market-backend.zip
```

### Step 6: Enable SSL/HTTPS

```bash
# Add App Service managed certificate (free)
az webapp config ssl bind \
  --resource-group mango-market-rg \
  --name mango-market-app \
  --certificate-path /subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.CertificateRegistration/certificateOrders/{order}
```

Or use Azure Key Vault for custom domains.

### Step 7: Configure CORS

Update CORS settings in Azure Portal > Configuration > General Settings:
```
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

### Step 8: Monitor & Logs

```bash
# View streaming logs
az webapp log tail \
  --resource-group mango-market-rg \
  --name mango-market-app

# Enable detailed logging
az webapp log config \
  --resource-group mango-market-rg \
  --name mango-market-app \
  --web-server-logging filesystem
```

---

## 🗄️ Database Configuration (Azure MySQL)

### Create Azure Database for MySQL

```bash
az mysql server create \
  --resource-group mango-market-rg \
  --name mango-mysql-server \
  --location eastus \
  --admin-user dbadmin \
  --admin-password YourStrongPassword123! \
  --sku-name B_Gen5_1 \
  --storage-size 51200
```

### Configure Firewall

```bash
# Allow access from App Service
az mysql server firewall-rule create \
  --resource-group mango-market-rg \
  --server mango-mysql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Create Database

```bash
az mysql db create \
  --resource-group mango-market-rg \
  --server-name mango-mysql-server \
  --name mango_market_db
```

### Update DB Connection in .env

```
DB_HOST=mango-mysql-server.mysql.database.azure.com
DB_USER=dbadmin@mango-mysql-server
DB_PASSWORD=YourStrongPassword123!
DB_NAME=mango_market_db
```

---

## 🔐 Security Best Practices

1. **HTTPS Only**: Enable in Azure Portal > SSL Settings > HTTPS Only
2. **API Authentication**: Implement JWT tokens for API endpoints
3. **Rate Limiting**: Configured in app (100 requests/hour by default)
4. **CORS**: Only allow trusted domains
5. **Secrets Management**: Use Azure Key Vault instead of .env in production
6. **Database SSL**: Enable SSL connections to MySQL
7. **IP Whitelisting**: Restrict database access to App Service only

---

## 📊 Performance Tuning

### Gunicorn Configuration
- **Workers**: Number of CPUs on App Service plan
- **Worker Class**: Use `sync` for I/O-bound apps
- **Timeout**: 120s (change if needed for long operations)

### Database Connection Pooling
Configured in `db_config.py`:
```python
pool_size=10
max_overflow=20
pool_recycle=3600
```

### Caching
Implement Redis for session caching:
```bash
# Create Azure Cache for Redis
az redis create \
  --resource-group mango-market-rg \
  --name mango-market-redis \
  --location eastus \
  --sku Basic \
  --capacity 0
```

---

## 🆘 Troubleshooting

### App won't start
```bash
az webapp log tail --resource-group mango-market-rg --name mango-market-app
```

### Database connection issues
- Check firewall rules allow App Service
- Verify DB_HOST DNS resolves correctly
- Ensure SSL is enabled if required

### Performance issues
- Increase App Service plan size (B2 → B3 → S1)
- Scale to multiple instances for load balancing
- Enable Application Insights for monitoring

### 502 Bad Gateway
- Check Gunicorn process (likely crashed)
- Verify startup command syntax
- Check application logs for errors

---

## 📈 Scaling

### Vertical Scaling (Bigger Instance)
```bash
az appservice plan update \
  --resource-group mango-market-rg \
  --name mango-market-plan \
  --sku S1
```

### Horizontal Scaling (More Instances)
```bash
az appservice plan update \
  --resource-group mango-market-rg \
  --name mango-market-plan \
  --number-of-workers 3
```

---

## 🔄 CI/CD Pipeline (Optional)

### Using GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: mango-market-app
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: './backend'
```

---

## 📞 Support

For Azure support: https://azure.microsoft.com/support/
For Flask/Python issues: https://flask.palletsprojects.com/
For Gunicorn docs: https://docs.gunicorn.org/
