import os

from .secrets import Secrets  # noqa


class Config:
    """Base configuration for the PyBioPharma server."""
    DEVELOPMENT = False
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'postgresql:///biopharma')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Security settings
    SECURITY_CONFIRMABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True

    SECURITY_EMAIL_SUBJECT_REGISTER = 'Welcome to BioPharma online'
    SECURITY_EMAIL_SUBJECT_CONFIRM = 'BioPharma: Please confirm your email'
    SECURITY_EMAIL_SUBJECT_PASSWORDLESS = 'BioPharma: Login instructions'
    SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE = 'BioPharma: Your password has been reset'
    SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = 'BioPharma: Your password has been changed'
    SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = 'BioPharma: Password reset instructions'

    # Settings for Celery
    CELERY_BROKER_URL = 'amqp://guest@localhost'
    CELERY_TIMEZONE = 'Europe/London'
    CELERY_ENABLE_UTC = True

    # We need a result backend to track task status.
    # However we don't need to store results, since tasks write to the DB.
    CELERY_RESULT_BACKEND = 'rpc://'
    CELERY_TASK_IGNORE_RESULT = True

    # We don't make use of rate limiting, so turn it off for a performance boost
    CELERY_WORKER_DISABLE_RATE_LIMITS = True

    # We expect to have few tasks, but long running, so don't reserve more than you're working on
    # (this works well combined with the -Ofair option to the workers, which is now default)
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_TASK_ACKS_LATE = True
    # Since tasks are long-running, we want to know if they are actually running
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_SOFT_TIME_LIMIT = 60 * 60 * 5  # 5 hours
    CELERY_TASK_TIME_LIMIT = 60 * 60 * 5.1  # Hard limit 6 mins longer

    # Just in case, restart workers once they've run this many jobs
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

    # How many worker processes to run
    CELERY_WORKER_CONCURRENCY = 4


class DevConfig(Config):
    """Variant configuration options for local developer machines."""
    DEVELOPMENT = True
    DEBUG = True

    # How many worker processes to run
    CELERY_WORKER_CONCURRENCY = 2
