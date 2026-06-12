from flask import Flask
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .logging_format import JsonFormatter


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
        gunicorn_error = logging.getLogger("gunicorn.error")
        gunicorn_access = logging.getLogger("gunicorn.access")

        json_formatter = JsonFormatter()

        for logger in [app.logger, gunicorn_error, gunicorn_access]:
            logger.setLevel(gunicorn_error.level)
            for handler in logger.handlers:
                handler.setFormatter(json_formatter)


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
