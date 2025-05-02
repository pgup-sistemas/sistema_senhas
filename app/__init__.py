import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Inicialização das extensões
login_manager = LoginManager()
db = SQLAlchemy()
socketio = SocketIO()

from .models import Usuario

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.Config')

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    from .routes.admin import init_login_manager
    init_login_manager(login_manager)

    # Importa e registra blueprints
    from .routes.public import public_bp
    from .routes.operator import operator_bp
    from .routes.admin import admin_bp
    from .routes.emissao import emissao_bp
    from .routes.admin_guiche import admin_guiche_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(operator_bp, url_prefix='/operador')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(emissao_bp, url_prefix='/emissao')
    app.register_blueprint(admin_guiche_bp, url_prefix='/admin/guiche')

    return app

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
