
from flask import Flask
from flask_security import SQLAlchemyUserDatastore

from . import views
from .admin import setup_admin
from .extensions import db, mail, migrate, security


def create_app(config_name=None):
    """Build our Flask application with the given config source.

    If no config_name is given, we default to biopharma.server.config.Config,
    unless overridden by the environment variable APP_SETTINGS.
    """
    if config_name is None:
        import os
        config_name = os.getenv('APP_SETTINGS', 'biopharma.server.config.Config')
    app = Flask(__name__)
    app.config.from_object(config_name)
    app.config.from_object('biopharma.server.config.Secrets')
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    setup_security(app, db)
    setup_admin(app)
    add_context_processors(app)
    app.register_blueprint(views.blueprint)
    return app


def add_context_processors(app):
    """Add context processors for this app."""
    from datetime import datetime

    app.jinja_env.add_extension('jinja2.ext.do')

    @app.context_processor
    def inject_now():
        """Enable {{now}} in templates, used by the footer."""
        return {'now': datetime.utcnow()}

    @app.context_processor
    def inject_status():
        """Provide the ExperimentStatus enum to all templates."""
        from .database import ExperimentStatus
        return {'ExperimentStatus': ExperimentStatus}

    @app.context_processor
    def inject_bokeh_version():
        """Provide the Bokeh version, used for plotting scripts and styles."""
        from bokeh import __version__
        return {'bokeh_version': __version__}


def setup_security(app, db):
    """Set up Flask-Security for this app."""
    from .database import User, Role
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security_ctx = security.init_app(app, datastore=user_datastore)

    @security_ctx.send_mail_task
    def delay_flask_security_mail(msg):
        """Send emails via a Celery task."""
        from .tasks import create_celery
        celery = create_celery(app)
        celery.send_task(
            'biopharma.send_mail',
            kwargs={'subject': msg.subject, 'sender': str(msg.sender),
                    'recipients': msg.recipients, 'body': msg.body,
                    'html': msg.html})

    @app.before_first_request
    def set_up_roles():
        """Set up initial roles."""
        # Create our roles -- unless they already exist
        user_datastore.find_or_create_role(
            name='admin', description='Administrator')
        user_datastore.find_or_create_role(
            name='experimenter', description='Is able to submit new experiments')

        # Commit any database changes
        db.session.commit()
