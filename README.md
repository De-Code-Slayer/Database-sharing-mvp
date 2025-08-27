# Database for MVP

A lightweight **shared database platform** built with **Flask + PostgreSQL**.  
It provides developers with a quick way to spin up and manage databases (like Heroku),  
with features for backups, external migrations, and environment variable provisioning.

---

## 🚀 Features
- Shared PostgreSQL connection pool (Heroku Postgres or custom DB)
- Connection pooling support (via PgBouncer)
- Backup & restore support
- Database migration to external PostgreSQL instances
- Auto-provision environment variables on database creation
- Configurable for **development** and **production**
- Logging included (file + console)

---

## 📂 Project Structure

---

## ⚙️ Configuration

Flask loads configs in this order:

1. **Base config (`config.py`)**  
   Defines `DevelopmentConfig`, `ProductionConfig`.

2. **Instance config (`instance/config.py`)**  
   Optional, contains **secrets/overrides** (ignored by git).  

Example:

```python
# config.py
class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://dev_user:pass@localhost/dev_db"

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
```