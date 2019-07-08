# Developing the PyBioPharma framework

NB: The instructions below are only relevant for people updating the project
infrastructure. Normal users should *not* run these commands!

This project is being developed using Python 3.5. It should work in 3.6 too.
The server is best run using Python 3.6 to benefit from ordered dictionaries.

Python dependencies are being managed with [pip-tools][].
The base requirements are listed in `requirements/base.in`.

To update the pinned versions run `make` in the `requirements` folder.

To see differences in your virtual environment with changed requirements, run
```
pip-sync -n requirements/local.txt
```

## Generating UML diagrams

The UML class diagram is produced with [PlantUML][].
To recreate it run:
```
java -jar ~/bin/plantuml.jar -tsvg docs/class_diagram.txt
```

[pip-tools]: https://github.com/nvie/pip-tools
[PlantUML]: http://plantuml.com
