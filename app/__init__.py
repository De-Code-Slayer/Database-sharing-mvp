

from flask import (Flask, request,
 render_template
)
import logger
from .config import config
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url
from flask_talisman import Talisman
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DisconnectionError
from .views.view_utils.filters import register_filters
from apscheduler.schedulers.background import BackgroundScheduler


# Load environment variables from .env file
load_dotenv()

# create the extension
db = SQLAlchemy()



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

   


    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # import db models
    from .database.models import User
    

    with app.app_context():
        # db.drop_all()
        db.create_all()

    #  register views
    from .views.api import api
    from .views.dashboard import dashboard
    

        # register blueprints
    app.register_blueprint(dashboard)
    app.register_blueprint(api, url_prefix="/api")


    # register filters 
    # register_filters(app)


    # setup login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'dashboard.sign_in'    
    login_manager.login_message_category ='info'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
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
        return render_template("error/pages-misc-error.html"), 500

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
    

    return app

app = create_app()
