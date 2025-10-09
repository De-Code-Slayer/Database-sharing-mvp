import eventlet
eventlet.monkey_patch()

from flask import (Flask, request,
 render_template,jsonify, url_for
)
from .logger import logger
from .config import config
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from authlib.integrations.flask_client import OAuth
from flask_cors import CORS



# Load environment variables from .env file
load_dotenv()

# create the extension
db = SQLAlchemy()
jwt = JWTManager()
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///mvp.db").replace("postgres://", "postgresql://"))
csrf = CSRFProtect()
socketio = SocketIO()
# Allow only your frontend domain
cors = CORS()

# Authlib OAuth setup
oauth = OAuth()

def patch_url_for(app):
    """Force url_for('static', ...) to return relative URLs even when SERVER_NAME is set."""
    original_url_for = url_for

    def patched_url_for(endpoint, **values):
        if endpoint == "static":
            # Remove _external or _scheme if they exist
            values.pop("_external", None)
            values.pop("_scheme", None)
            # Build normal relative URL
            return f"/static/{values.get('filename', '')}"
        return original_url_for(endpoint, **values)
    app.jinja_env.globals['url_for'] = patched_url_for
    


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, subdomain_matching=True)
    env = os.environ.get("FLASK_ENV", "development")
    print(f"env: {os.getenv('FLASK_ENV')}")
   
    patch_url_for(app)


    
    if test_config is None:
     # Normal mode: load dev/prod config
        app.config.from_object(config[env])
        # Also allow instance/config.py (for local secrets, gitignored)
        app.config.from_pyfile("config.py", silent=True)
       
    else:
        # Testing mode: load test config dict
        app.config.from_mapping(test_config)
   
    # init flask migrate
    migrate = Migrate(app, db)
    


    # initialize the app with the extension
    db.init_app(app)
    # initialize socketio AFTER app is created
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    jwt.init_app(app)
    cors.init_app(app, origins=["https://smallshardz.com","www.smallshardz.com","https://dashboard.smallshardz.com"])
    oauth.init_app(app)

   


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # import db models
    from .database.models import MyUser
    

    with app.app_context():
        # db.drop_all()
        db.create_all()

    #  register views
    from .views.api.api import api_bp
    from .views.auth.auth import auth
    from .views.dashboard.dashboard import dashboard_bp
    from .views.terminal.terminal import terminal_bp
    
     # Register all blueprints
    blueprints = [dashboard_bp, api_bp, auth, terminal_bp]

    for bp in blueprints:
        # Disable subdomains in dev
        if os.getenv("FLASK_ENV") == "development":
            bp.subdomain = None
        app.register_blueprint(bp)
    #     # register blueprints
    # app.register_blueprint(dashboard_bp)
    # app.register_blueprint(api_bp)
    # app.register_blueprint(auth)
    # app.register_blueprint(terminal_bp)


    # register filters 
    # register_filters(app)


    # setup login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'    
    login_manager.login_message_category ='info'
    

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return MyUser.query.get(int(user_id))
        except Exception as e:
            db.session.rollback()
            print(f'=========== Cant get user loaded {e}===========')


    # error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template("error/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        # note that we set the 500 status explicitly
        return jsonify({"status":"failed", "error":str(e)}), 500

    @app.errorhandler(401)
    def unauthorized(e):
        # note that we set the 500 status explicitly
        return render_template("error/401.html"), 500
    
    

    @app.before_request
    def log_request():
        logger.info({
            "event": "http_request",
            "method": request.method,
            "path": request.path,
            "host": request.host,
            "remote_addr": request.remote_addr,
        })

    @app.after_request
    def log_response(response):
        logger.info({
            "event": "http_response",
            "status": response.status_code,
            "path": request.path,
        })
        return response
    

    from apscheduler.schedulers.background import BackgroundScheduler
    from .cron.job import run_billing_cron
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_billing_cron, trigger="cron", hour=0)  # run daily at midnight
    scheduler.start()



    return app

app = create_app()


