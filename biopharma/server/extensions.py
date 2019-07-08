from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import Security


db = SQLAlchemy()
migrate = Migrate()

mail = Mail()
security = Security()
admin = Admin(name='BioPharma Admin')
