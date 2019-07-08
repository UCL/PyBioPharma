# Template secrets file for BioPharma
#
# This shows what secret configuration options are needed by the application.
# Settings from the non-exemplar version of this file will be merged into the
# active configuration.


class Secrets:
    # The Flask secret key
    SECRET_KEY = "Change this please!"

    # Email settings
    MAIL_DEFAULT_SENDER = "BioPharma online <a.person@domain.com>"
    MAIL_SERVER = "smtp.domain.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None

    SECURITY_PASSWORD_SALT = 'Change this please!'
