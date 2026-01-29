from flask import Flask
import config


def create_app():
    app = Flask(
        __name__,
        static_folder='../static',
        template_folder='templates',
    )
    app.config['SECRET_KEY'] = config.SECRET_KEY

    from app.models import TaskDB
    app.db = TaskDB(config.DATABASE_PATH)

    from app.routes import bp
    app.register_blueprint(bp)

    return app
