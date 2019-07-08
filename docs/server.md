# Running the PyBioPharma server

NB. These instructions are oriented at developers, and hence are not as detailed as for other aspects of the system.

## Install extra requirements

```bash
pip install -r requirements/server.txt
```

## Configure environment

```bash
export FLASK_APP=biopharma.server.autoapp
export FLASK_DEBUG=True
export APP_SETTINGS=biopharma.server.config.DevConfig
```

## Configure secrets

Copy the file `biopharma/server/config/secrets.example.py` as `biopharma/server/config/secrets.py`
and fill in suitable values.

You can get Python to generate a suitable secret key, e.g. with
```python
import secrets
print(secrets.token_hex(32))
```

Configuring email sending will depend on available providers.
There are example [instructions for using your GMail credentials here](https://stackoverflow.com/questions/37058567/configure-flask-mail-to-use-gmail).

## Install the background task queue

We use Celery for this with the RabbitMQ broker. The former has already been installed with `pip`; the latter needs to be set up following the instructions at <http://docs.celeryproject.org/en/latest/getting-started/brokers/rabbitmq.html>.

### Create a database and run migrations

These commands should be run from the root folder of the repository.

To create a fresh database on a new (development) system:
```bash
createdb --echo biopharma
```

To create new migrations if the models change:
```bash
flask db migrate
# Review migrations folder manually, add to version control
```

To apply any new migrations to prepare an existing database for use:
```bash
flask db upgrade
```

## Run the task queue

For a simple development setup, in a separate terminal run:
```bash
PATH=/usr/local/sbin:$PATH
export RABBITMQ_NODE_IP_ADDRESS=127.0.0.1
rabbitmq-server -detached
celery worker -A biopharma.server.tasks.worker.celery --loglevel=info
```

You can stop the worker using Control-C, and then the broker with
```bash
rabbitmqctl stop
```

## Run the webapp

```bash
flask run
```

## Set up an admin user

Once an initial user has registered, you can promote them to admin using:
```bash
flask roles add <user_email> admin
```

Once you have one admin user, the admin interface can also be used for this.


# Extending the BioPharma server

Most changes to the existing model structure should be picked up automatically by the server functionality.
For instance, new component parameters, or parameters with changed types or descriptions,
will be reflected in the experiment setup tabs.
Changes to the files in `/data` will update the default values for parameters in the web interface.
However, some model changes will require editing the server code as well.
Examples of these include:
- creating a new unit operation (process step)
- changing the objectives that web users can optimise
- changing the result visualisations

All server code is contained within the [biopharma/server](../biopharma/server) folder.
The files and folders within here are as follows:
- `config`: settings for the application
- `forms`: generating the forms for submitting a new experiment, and processing form input
- `tasks`: running an experiment
- `templates`: the site look and feel, page HTML, etc.
- `admin.py`: the admin interface
- `app.py` and `autoapp.py`: pulling the pieces together
- `database.py` and `extensions.py`: setting up some of the Flask modules used
- `model.py`: links the web interface to the process economics model,
  defining the default facility setup and process sequence
- `plotting.py`: generates result graphs
- `views.py`: handles web page requests

Pointers on how to make various changes are given in sections below.
Files not mentioned below are less likely to require changes,
because they control the basic functionality of the server.

## Incorporating a new unit operation

Once the [new source file and class have been added and tested](usage.md#implementing-process-steps-unit-operations),
you need to edit [model.py](../biopharma/server/model.py) to make it available in the web interface.
The `create_facility()` method there creates a default facility and process sequence.
Simply add your operation to the list of steps there, optionally replacing an existing step.

## Changing the available objectives and optimiser settings

There are two parts to this.

1. In [forms/optimiser.py](../biopharma/server/forms/optimiser.py)
   edit the `make_optimiser_form()` function to define the checkboxes available.
   Make sure that fields defining objectives have variable names beginning `obj_`,
   and that those defining parameters to be optimised have names beginning `var_`,
   as for the existing fields.
2. In [forms/assign.py](../biopharma/server/forms/assign.py)
   modify the `assign_parameters()` function to read these form fields and configure
   the optimiser accordingly.
   Hopefully the existing cases will give sufficient guidance on what is needed.

## Changing result visualisations

Firstly, you need to add a function to [plotting.py](../biopharma/server/plotting.py) to create the desired plot.
If you are just altering an existing plot, you can edit one of the existing functions and that should be sufficient.

If creating a new plot you also need to extend the HTML to use it.
Edit the `results()` function in [views.py](../biopharma/server/views.py) to call your new function and pass the result to the `render_template` call.
Then edit [templates/opt_results.html](../biopharma/server/templates/opt_results.html) to add a `<figure>` block, similarly to the existing plots, which uses your new variables.

## Adding a new static page

You will need to add a handler for the page in [views.py](../biopharma/server/views.py),
and a corresponding template to display within the [templates](../biopharma/server/templates/) folder.
The `index` page is the simplest example to start with.
