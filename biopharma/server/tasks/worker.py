
import io
import traceback
import sys

from . import create_celery, SoftTimeLimitExceeded
from ..app import create_app
from ..database import Experiment, ExperimentStatus


celery = create_celery(create_app())


class DatabaseIO(io.StringIO):
    """Writes to a database field as well as the underlying class' buffer."""

    def __init__(self, entity, fieldname, *args, **kwargs):
        """Create a DatabaseIO object.

        :param entity: the database row (Model instance) to write to
        :param fieldname: the column name to write to
        """
        self._entity = entity
        self._fieldname = fieldname
        super().__init__(*args, **kwargs)

    def write(self, s):
        """Write a string to the buffer & DB."""
        e, fn = self._entity, self._fieldname
        kwargs = {
            fn: getattr(e, fn) + s,
            'commit': '\n' in s
        }
        e.update(**kwargs)
        super().write(s)

    def close(self):
        """Ensure all output is flushed to the DB."""
        self._entity.save()
        super().close()


@celery.task(name='biopharma.optimise')
def optimise(expt_id):
    """Celery task to run an optimisation, handling timeout & error/output logging."""
    expt = Experiment.query.get(expt_id)
    if expt is None:
        return  # Invalid / deleted id; ignore
    log = DatabaseIO(expt, 'log')
    from contextlib import redirect_stdout
    with redirect_stdout(log):
        try:
            expt.update(status=ExperimentStatus.running)
            run_optimisation(expt)
        except SoftTimeLimitExceeded:
            # Log & display time limit exceeded
            print('\n\nTime limit exceeded - optimisation terminated!')
            expt.update(status=ExperimentStatus.error)
        except Exception as e:
            # Log & display unexpected error
            print('\n\nUnexpected error running optimisation!\n' + traceback.format_exc())
            expt.update(status=ExperimentStatus.error)
            print('Error running experiment {}: {}'.format(expt_id, traceback.format_exc()),
                  file=sys.stderr)
        finally:
            log.close()


def run_optimisation(expt):
    """Actually run the given optimisation experiment."""
    from datetime import datetime
    from ..model import create_default
    from ..forms import assign_parameters

    optimiser, steps = create_default()
    assign_parameters(expt.form_data, optimiser)
    optimiser.run()
    # Store results in DB
    results = optimiser.save_results()
    expt.update(
        status=ExperimentStatus.finished,
        completed=datetime.now(),
        results=results)


@celery.task(name='biopharma.send_mail')
def send_mail(**kwargs):
    """Send an email message using Flask-Mail."""
    from flask import current_app
    from flask_mail import Mail, Message

    mail = Mail(current_app)
    mail.send(Message(**kwargs))
