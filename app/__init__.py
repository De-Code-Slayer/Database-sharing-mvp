

from flask import (Flask, request,
 render_template,jsonify
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



# Load environment variables from .env file
load_dotenv()

# create the extension
db = SQLAlchemy()
jwt = JWTManager()
engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///mvp.db").replace("postgres://", "postgresql://"))
csrf = CSRFProtect()
socketio = SocketIO()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    env = os.environ.get("FLASK_ENV", "development")
    
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
    socketio.init_app(app)
    jwt.init_app(app)

   


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
    

        # register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth)
    app.register_blueprint(terminal_bp)


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
        return jsonify({"status":"failed", "error":e}), 500

    @app.errorhandler(401)
    def unauthorized(e):
        # note that we set the 500 status explicitly
        return render_template("error/page-misc-unauthorized.html"), 500
    


    @app.before_request
    def log_request():
        logger.info({
            "event": "http_request",
            "method": request.method,
            "path": request.path,
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


