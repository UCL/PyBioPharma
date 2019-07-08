
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for
)
from flask_security import current_user, login_required, roles_accepted

from .database import Experiment, ExperimentStatus
from .plotting import make_cost_plot, make_sample_scatter_plot

blueprint = Blueprint('main', __name__)


@blueprint.route('/')
def index():
    """The main index page for the application."""
    return render_template('index.html')


@blueprint.route('/experiments')
@login_required
def experiments():
    """Show all (my) submitted experiments."""
    return render_template(
        'experiments.html',
        experiments=current_user.experiments.order_by(Experiment.submitted.desc()).all())


@blueprint.route('/results/<int:expt_id>')
@login_required
def results(expt_id):
    """Show the results of a completed experiment."""
    expt = Experiment.query.get_or_404(expt_id)
    if expt.user != current_user and not current_user.has_role('admin'):
        abort(403)

    from .model import create_default
    from .forms import assign_parameters

    optimiser, steps = create_default()
    assign_parameters(expt.form_data, optimiser)
    optimiser.load_results(expt.results)

    cost_script, cost_div = make_cost_plot(optimiser)
    col_script, col_div = make_sample_scatter_plot(optimiser)

    return render_template(
        'opt_results.html',
        expt=expt,
        optimiser=optimiser,
        cost_script=cost_script,
        cost_div=cost_div,
        col_script=col_script,
        col_div=col_div)


@blueprint.route('/view_log/<int:expt_id>')
@login_required
def view_log(expt_id):
    """Show the log from a running/finished experiment."""
    expt = Experiment.query.get_or_404(expt_id)
    if expt.user != current_user and not current_user.has_role('admin'):
        abort(403)
    return render_template('view_log.html', expt=expt)


@blueprint.route('/delete/<int:expt_id>')
@login_required
def delete(expt_id):
    """Delete a completed experiment."""
    expt = Experiment.query.get_or_404(expt_id)
    if expt.user != current_user and not current_user.has_role('admin'):
        abort(403)
    expt.delete()
    flash('The experiment has been deleted', 'success')
    return redirect(url_for('main.experiments'))


def get_git_hash():
    """Get the SHA1 for the latest commit of the server code.

    Helper function for experiment creation.
    """
    from subprocess import check_output
    repo_path = current_app.root_path
    return check_output(
        ['git', '-C', repo_path, 'rev-parse', 'HEAD']).decode().strip()


@blueprint.route('/setup_opt', methods=('GET', 'POST'))
@login_required
@roles_accepted('admin', 'experimenter')
def setup_opt():
    """Forms to set up (and submit) an optimisation run."""
    from .model import create_default
    from .forms import make_all_forms
    from .tasks import create_celery

    optimiser, steps = create_default()
    form = make_all_forms(optimiser)
    if form.is_submitted():
        if form.validate():
            # print(form.data)
            flash('Optimisation job submitted', 'success')
            expt = Experiment.create(
                code_version=get_git_hash(),
                form_data=form.data,
                status=ExperimentStatus.submitted,
                user_id=current_user.id,
                name=form.name_field.data,
            )
            celery = create_celery(current_app)
            celery.send_task(
                'biopharma.optimise',
                args=(expt.id,))
            expt.update(status=ExperimentStatus.queued)
            return redirect(url_for('main.experiments'))
        else:
            # TODO: It might be neat to make these clickable, for showing the relevant tab,
            # but this is very minor!
            # TODO: List each error in a ul.
            print(form.errors)
            error_forms = [form[field].label.text
                           for field in form.errors
                           if form[field].type == 'FormField']
            error_fields = [form[field].label.text
                            for field in form.errors
                            if form[field].type == 'StringField']
            if error_forms:
                flash(
                    'There are issues with your settings in the following tabs: {}'.format(
                        ', '.join(error_forms)),
                    'error')
            if error_fields:
                flash(
                    'There are issues with your settings in the following fields: {}'.format(
                        ', '.join(error_fields)),
                    'error')
            if not (error_forms or error_fields):
                flash('Your security token has expired; please re-submit', 'error')

    return render_template(
        'setup_opt.html',
        steps=steps,
        optimiser=optimiser,
        form=form)
