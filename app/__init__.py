import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from markupsafe import Markup
from flask_migrate import Migrate
from datetime import datetime
import pytz
from dotenv import load_dotenv

# .env файлын жүктеу (локальды компьютер үшін)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def nl2br(value):
    if not value:
        return ""
    escaped_value = Markup.escape(value)
    return escaped_value.replace('\n', Markup('<br>\n'))

def create_app():
    app = Flask(__name__)
    
    # --- ДЕРЕКҚОРДЫ БАПТАУ (ЕҢ МАҢЫЗДЫ ЖЕРІ) ---
    # Render-де DATABASE_URL бар, компьютерде жоқ.
    database_url = os.environ.get('DATABASE_URL')
    
    # Render кейде "postgres://" береді, ал жаңа SQLAlchemy-ге "postgresql://" керек.
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Егер database_url бар болса (Render) соны қолданамыз, болмаса компьютердегі файлды
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///../instance/database.db'
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    
    # Почта баптаулары
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT') or 587)
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'main.login'
    login_manager.login_message = None 

    app.jinja_env.filters['nl2br'] = nl2br
    
    @app.template_filter('to_local_time')
    def to_local_time_filter(utc_datetime):
        if utc_datetime is None:
            return ""
        local_tz = pytz.timezone('Asia/Almaty') 
        local_dt = utc_datetime.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_dt.strftime('%d.%m.%Y в %H:%M')

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app