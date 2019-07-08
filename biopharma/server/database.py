
from enum import Enum

from flask_security import UserMixin, RoleMixin
from sqlalchemy.sql import func

from .extensions import db


class CRUDMixin(object):
    """Mixin that adds convenience methods for CRUD (create, read, update,
       delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it in the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()


class Model(CRUDMixin, db.Model):
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True


class ExperimentStatus(Enum):
    """Possible statuses for a BioPharma experiment."""
    submitted = 1
    queued = 2
    running = 3
    finished = 4
    error = 5


class Experiment(Model):
    """Stores details of optimisation experiments run."""
    id = db.Column(db.Integer, primary_key=True)

    # Git commit hash of the version of the model run
    code_version = db.Column(db.String(50), nullable=False)

    # Parameters for the experiment - a pickled dictionary
    form_data = db.Column(db.PickleType(), nullable=False)

    # Experiment status - queued, running, finished, error
    status = db.Column(db.Enum(ExperimentStatus), nullable=False)

    # Any printed output from the experiment as it ran
    log = db.Column(db.Text, server_default='')

    # Results
    results = db.Column(db.Text, nullable=True)

    # Info on when it ran
    submitted = db.Column(db.DateTime, nullable=False, server_default=func.now())
    completed = db.Column(db.DateTime, nullable=True)

    # Who owns this experiment
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    # An optional name for the experiment
    name = db.Column(db.String(50), server_default='')

    def __repr__(self):
        return '<Experiment {}{}: submitted={}, status={}>'.format(
            self.id, ' ({})'.format(self.name) if self.name else '',
            self.submitted, self.status.name)


# ------------------------------------------------------------
# User & security models
# ------------------------------------------------------------


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
                       )


class Role(Model, RoleMixin):
    """Stores roles that users can have."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        """Provide a human-readable display for Flask-Admin."""
        return self.name


class User(Model, UserMixin):
    """Stores users of the BioPharma website."""

    # Flask-security core fields
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)

    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic'))

    # For confirming email addresses
    confirmed_at = db.Column(db.DateTime)

    # For tracking user visits
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)

    # Our extra fields
    created = db.Column(db.DateTime, server_default=func.now())
    experiments = db.relationship(
        'Experiment',
        backref='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
        passive_deletes=True)

    def __str__(self):
        """Provide a human-readable display for Flask-Admin."""
        return self.email

    @property
    def can_run_expt(self):
        """Return whether a user can launch experiments."""
        return self.has_role('experimenter') or self.has_role('admin')

    @property
    def is_admin(self):
        """Return whether a user has admin access."""
        return self.has_role('admin')
