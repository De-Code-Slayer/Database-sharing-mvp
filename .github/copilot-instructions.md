# Database Sharing Platform - AI Coding Guidelines

## Architecture Overview
This is a multi-tenant Flask web application that provides users with managed database instances and file storage. The platform creates isolated PostgreSQL databases per user while maintaining a central application database for user management and billing.

### Core Components
- **Flask App Factory**: `create_app()` in `app/__init__.py` initializes extensions (SQLAlchemy, SocketIO, JWT, OAuth, CORS)
- **Database Models**: Central models in `app/database/models.py` (MyUser, DatabaseInstance, StorageInstance, Subscription, Invoice)
- **Tenant Databases**: Dynamic PostgreSQL database creation via `create_postgres_tenant()` in `app/views/utilities/database.py`
- **Real-time Terminal**: Flask-SocketIO enables web-based database terminal access
- **File Storage**: Quota-managed storage with upload/download via `app/views/utilities/storage.py`
- **Billing System**: Subscription-based with Paystack integration and automated invoice generation

### Key Patterns
- **Blueprint Organization**: Views organized as blueprints (`api`, `auth`, `dashboard`, `terminal`, `payment`)
- **Utility Functions**: Business logic in `app/views/utilities/` (database, storage, payment, auth, migration)
- **API Authentication**: JWT tokens and API keys for programmatic access
- **Background Jobs**: APScheduler for daily billing cron jobs
- **Environment Config**: Flask environments (development/production) with instance config overrides

## Development Workflow
### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (.env file)
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost/app_db
SECRET_KEY=your_secret
PAYSTACK_PUBLIC_KEY=pk_test_...

# Run with SocketIO support
python run.py
# Or: flask run (but loses SocketIO features)
```

### Database Operations
```bash
# Create migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Create tenant database (programmatically via web UI)
# Access at: http://dashboard.smallshardz.com/terminal/<db_id>
```

### Testing
```bash
# Run tests
pytest

# Test with coverage
pytest --cov=app --cov-report=html
```

## Deployment
### Heroku (Development/Staging)
- Uses `Procfile` with Gunicorn
- Environment variables set in Heroku dashboard
- PostgreSQL via Heroku Postgres add-on

### EC2 Production (Amazon Linux)
- Systemd service: `smallshardz.service`
- Nginx reverse proxy (not shown)
- GitHub Actions deployment workflow
- Custom migration scripts: `migrate_pg.sh`

## Common Patterns
### Creating Database Tenants
```python
# In app/views/utilities/database.py
def create_postgres_tenant():
    username = sanitize_username(f"user_{current_user.username}_{secrets.token_hex(4)}")
    database_name = f"db_{secrets.token_hex(4)}"
    password = secrets.token_urlsafe(16)
    
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"CREATE USER {username} WITH PASSWORD :password"), {"password": password})
        conn.execute(text(f"CREATE DATABASE {database_name} OWNER {username}"))
    
    create_subscription('postgres', database_name)
    return {"database": database_name, "username": username, "password": password, "uri": connection_url}
```

### File Upload with Quota Check
```python
# In app/views/utilities/storage.py
def upload_file(request):
    file = request.files['file']
    storage = get_user_storage()
    
    if storage.used_space + file_size > storage.quota:
        return {"error": "Storage quota exceeded"}
    
    # Save file and update quota
    storage.used_space += file_size
    db.session.commit()
```

### API Authentication
```python
# In app/views/api/helper.py
def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            abort(401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'])
            current_user_id = payload['user_id']
        except:
            abort(401)
        return f(*args, **kwargs)
    return decorated
```

### SocketIO Terminal Session
```python
# In app/views/terminal/terminal.py
@socketio.on("execute_command")
def handle_command(data):
    command = data.get("command")
    db_instance = get_database_instance(session["db_id"])
    
    # Execute psql command in subprocess
    process = subprocess.Popen(
        ["psql", db_instance.uri],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(command)
    emit("command_output", {"output": stdout, "error": stderr})
```

## Important Notes
- **Eventlet Monkey Patching**: Must be first import in `run.py` for SocketIO compatibility
- **Database URI Handling**: Always use `postgresql://` prefix (not `postgres://`)
- **Subdomain Routing**: Blueprints use subdomains in production (`api.smallshardz.com`, `dashboard.smallshardz.com`)
- **Storage Paths**: Files stored on disk with database tracking; use absolute paths
- **Billing Cron**: Runs daily at midnight via APScheduler to generate invoices
- **Migration Scripts**: Custom bash scripts for PostgreSQL dump/restore between servers
- **API Keys**: Generated once and hashed; only plain key shown to user immediately after creation

## Security Considerations
- CSRF protection enabled via Flask-WTF
- Talisman for security headers
- JWT for API authentication
- OAuth integration with Google/GitHub
- Password hashing with Werkzeug
- Input sanitization for database names/usernames</content>
<parameter name="filePath">c:\Users\User\OneDrive\Desktop\work space dev job\Database Sharing\.github\copilot-instructions.md