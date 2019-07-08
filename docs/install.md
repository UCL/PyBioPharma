# Installing PyBioPharma

## Installing Python and Git

The simplest way to install Python is using the [Anaconda][] distribution,
which is available for Windows, Mac OS and Linux. We suggest following the
[installation instructions provided by Software Carpentry][anaconda-swc].
Software Carpentry also provide [instructions on installing Git][git-swc].

[Anaconda]: https://www.continuum.io/downloads
[anaconda-swc]: http://swcarpentry.github.io/workshop-template/#python
[git]: https://git-scm.com/
[git-swc]: http://swcarpentry.github.io/workshop-template/#git

## Obtaining the PyBioPharma software

While the software can be downloaded from GitHub as a ZIP file and unpacked
on your computer, we recommend using [git][] to download it instead. This
will make it easier to obtain updated versions, and to keep track of your
own modelling work using the software. See [usage.md](usage.md) for more
about this.

First you need to open a terminal. On Windows, we suggest using the "Anaconda
Prompt" which is installed as part of Anaconda. You can also use "Git Bash"
(installed with Git) if you selected to add Anaconda to your PATH when it was
installed (this is no longer the default, however). On Mac OS the default app
is called "Terminal", or pick your favourite if you are familiar with these!
Unfortunately the commands to run are in places slightly different depending
on which terminal you use. There are thus two variants given within this
documentation: one for Windows-style terminals like "Anaconda Prompt", and
one for Unix-style terminals on Mac OS, Linux, or Git bash on Windows.

Within the terminal, change directory to where you want to store the PyBioPharma
files. For instance, you could use the following commands to store them
within a subfolder of your 'Desktop' folder.

On Windows with Anaconda Prompt:
```powershell
cd /D %HOMEDRIVE%%HOMEPATH%
cd Desktop
```

On Linux, Mac OS, or Windows with Git Bash:
```sh
cd
cd Desktop
```

The first line takes you to your 'home' folder, and the second to the
'Desktop' folder within that. If instead you wanted to install it in a
'Modelling' folder in your Dropbox folder, you might use the commands:

```sh
cd
cd Dropbox/Modelling
```

You can then use `git` to download PyBioPharma from GitHub:

```sh
git clone https://github.com/UCL-Biochemical-Engineering/PyBioPharma.git
```

This will create a 'PyBioPharma' folder in the directory you navigated to
above, containing all the files from the GitHub repository.

## Installing PyBioPharma itself

Having downloaded the software, you can then install it by running further
commands in your terminal. Following on from the above, we first change
into the new PyBioPharma folder, then create a 'virtual environment' to
store the installed software with its dependencies, then perform the
installation.

On Windows running Anaconda Prompt (or PowerShell or Command), use:
```sh
cd PyBioPharma
conda create -n biopharma python==3.6
activate biopharma
pip install -r requirements/local.txt
pip install -e .
```

On Mac OS and Linux, or Windows running Git Bash, the third command is
slightly different:
```sh
cd PyBioPharma
conda create -n biopharma python==3.6
source activate biopharma
pip install -r requirements/local.txt
pip install -e .
```

Changing directory and running the `activate biopharma` or
`source activate biopharma` line will need to be done each time you wish
to work with this software. The others are only required on first install.

## Background and explanation

It may be helpful to explain a little more about what some of the above steps
are doing.

The `git clone` creates a copy of the GitHub repository on your computer. It
contains not just the latest version of the software, but also the history of
all the changes that have been made since the software was created, stored
within hidden files managed by the `git` program. You can also use `git` to
keep track of changes you make, keeping parallel lines of history within the
repository. For instance, one line would track the official released version
(this is typically called 'master'), one could track your experimental work,
and one could refer to the version used for a particular publication. For more
about using `git` in this way see the file [git.md](git.md).

The `conda create` line sets up a new 'virtual enironment' for running the
software in. It is a way of isolating a collection of (Python) software from
the rest of your computer, so you can have different versions of the same
software installed without them interfering with each other. Our instructions
recommend using a conda environment for PyBioPharma mainly because it avoids
any issues arising if users update the main Python on their machine, or one
of the libraries that PyBioPharma uses, and in doing so make PyBioPharma stop
working. However, conda is also useful if you want to work with 2 different
versions of PyBioPharma on the same computer, as you can install them within
2 separate conda environments and then they won’t conflict with each other.

To do so, simply change the environment name used in the instructions above.
For instance, instead of `-n biopharma` use `-n new_biopharma`, and change
`source activate biopharma` to `source activate new_biopharma`. The
`pip install` commands remain the same.

If you are using multiple virtual environments for different PyBioPharma
versions, you will also want to have a separate `git clone` of the repository
for each one. (It is possible to avoid doing this, but gets confusing!)
The git clone and conda environment are separate - in a sense the former stores
the source for the program, and the latter stores the installed program - but
it is typical to have one conda environment per git clone. If you're wanting
to run models based on each clone and the equations are different, this will
be the case. If however a clone is essentially 'read only', i.e. you don’t want
to run the model given in that clone, you don’t need a conda environment for it.
