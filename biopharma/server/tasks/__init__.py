
# The core tools need to work without celery installed
try:
    from celery import Celery
    from celery.exceptions import SoftTimeLimitExceeded
except ImportError:
    class SoftTimeLimitExceeded(Exception):
        """Fake Celery timeout error."""
        pass


def create_celery(flask_app):
    """Initialise a Celery instance for this Flask app."""
    celery = Celery(flask_app.import_name,
                    broker=flask_app.config['CELERY_BROKER_URL'],
                    backend=flask_app.config['CELERY_RESULT_BACKEND'])
    celery.config_from_object(flask_app.config, namespace='CELERY')

    # Change the base Celery Task class to have Flask's app context
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    return celery
