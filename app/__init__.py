from flask import Flask
from app.extensions.db import db

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///datasets.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.routes.main_routes import bp as main_bp
    from app.routes.dataset_routes import bp as dataset_bp
    from app.routes.clustering_routes import bp as clustering_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(clustering_bp)

    with app.app_context():
        db.create_all()

    return app