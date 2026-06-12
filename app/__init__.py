from flask import Flask
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_logging(app)

    from .routes import bp
    app.register_blueprint(bp)

    configure_proxy(app)
    return app


def configure_logging(app):
    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger("gunicorn.error")

        # Sync log levels and handlers
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)


def configure_proxy(app):
    """Add werkzeug fixer to detect headers applied by upstream reverse proxy"""
    if app.config.get('PREFERRED_URL_SCHEME', '').lower() == 'https':
        app.wsgi_app = ProxyFix(
            app=app.wsgi_app,

            # trust X-Forwarded-Host
            x_host=1,

            # trust X-Forwarded-Port
            x_port=1,
        )
