
from flask import abort, redirect, request
from flask_security import current_user
from flask_security.utils import url_for_security
from flask_admin import AdminIndexView
from flask_admin.contrib import sqla

from .extensions import admin, db


class AccessMixIn:
    """Handle our access permissions."""

    def is_accessible(self):
        """Only allow users with the 'admin' role to view."""
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        """Redirect users when a view is not accessible."""
        if current_user.is_authenticated:
            # permission denied
            abort(403)
        else:
            # login
            return redirect(url_for_security('login', next=request.url))


class RestrictedIndexView(AccessMixIn, AdminIndexView):
    """Only admin users can view the index."""


class AdminModelView(AccessMixIn, sqla.ModelView):
    """Customised base class for admin model views."""
    can_create = False

    # Automatically display human-readable names for joined items
    column_auto_select_related = True


class RoleModelView(AdminModelView):
    """Customised view for Role model."""
    can_delete = False
    can_edit = False


class UserModelView(AdminModelView):
    """Customised view for User model."""
    column_filters = ('roles',)

    column_exclude_list = ('experiments', 'password')
    column_details_exclude_list = ('experiments', 'password')
    form_excluded_columns = ('experiments', 'password')

    def scaffold_list_columns(self):
        """Add roles to displayed columns."""
        cols = super().scaffold_list_columns()
        cols.append('roles')
        return cols


class ExperimentModelView(AdminModelView):
    """Customised view for Experiment model."""
    can_edit = False
    can_view_details = True

    column_display_pk = True
    column_filters = ('status', 'user.email')
    column_exclude_list = ('form_data', 'log', 'results')


def setup_admin(app):
    """Configure the admin interface for this app."""
    admin.init_app(app, index_view=RestrictedIndexView())

    from .database import Experiment, Role, User

    admin.add_view(RoleModelView(Role, db.session, name='Roles'))
    admin.add_view(UserModelView(User, db.session, name='Users'))
    admin.add_view(ExperimentModelView(Experiment, db.session, name='Experiments'))
