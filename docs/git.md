# Using git for modelling with PyBioPharma

Using the git version control system to store your work with PyBioPharma has
several benefits, both for you and the wider research group.

1. It keeps track of previous versions of your work, allowing you to go back to
   previously-working versions, or find the version that was used to produce a
   particular paper or result.
2. It lets you track different versions of the code simultaneously, so you can
   have a 'personal' version that you are playing with, or adding new features
   to, at the same time as the main (or master) version.
3. It lets you propose your changes to be merged with the master version for
   others to use.
4. It helps when collaborating with others on making changes to the models,
   keeping track of who does what and making sure modifications can be combined
   cleanly.
5. It can keep a central backup of everyone's work with the framework on
   GitHub, so it is available to future researchers.

Describing fully how to use git to achieve this would be beyond the scope of
this guide. For a good introduction to git we recommend the
[Software Carpentry git lesson](http://swcarpentry.github.io/git-novice/),
which you can follow at your own pace online or come to one of our workshops.
For more on the branching techniques discussed below, try the interactive
online tutorial at http://learngitbranching.js.org/?demo

Key terminology:
* A _branch_ is git's term for a parallel version of your project. By
  convention the main branch (the official version if you like) is called
  'master'.
* A _commit_ is a snapshot of the state of your project stored within the
  repository.

Below I cover some common tasks:
* creating a new branch for your work
* saving your work as a commit
* upgrading to a new version of PyBioPharma
* merging new changes from the master (main) branch into your own
* sharing your changes with others

All the commands below assume that you are in a terminal, in the folder
containing your PyBioPharma clone, and have activated your conda environment
(e.g. with `source activate biopharma`).


## Creating a new branch for your work

It is recommended to use self-explanatory names for branches, to help you (and
others) remember what they're about. For personal branches, it helps to avoid
name conflicts if you include your own name in the branch name. Note that
branch names are case sensitive: 'jonathan' is different from 'Jonathan'.

To create a new branch named 'jonathan/experimental' do

```sh
git checkout -b jonathan/experimental
```

As well as creating the branch this makes it the current branch, so that
subsequent commits will go on this branch.

To change to an already existing branch use just

```sh
git checkout jonathan/experimental
```


## Saving your work as a commit

First you need to use `git add` to tell git what changes you want to make part
of the commit, then use `git commit` to do the commit. See
http://swcarpentry.github.io/git-novice/04-changes/ for more details.

You will then want to 'push' your changes to GitHub, so a copy of your work is
stored there, not just on your local machine. Do this with the command

```sh
git push
```

The first time you run this for a new branch you will be told
"fatal: The current branch test has no upstream branch." Use the command
suggested by git to create a new branch in GitHub matching your new local
branch.

See http://swcarpentry.github.io/git-novice/07-github/ for more about working
with GitHub.


## Upgrading to a new version of PyBioPharma

If you want to take advantage of new features, you can use the following
commands. They assume your working copy is clean, i.e. any changes have been
committed already. The parts from `#` onwards are just comments - you don't
need to copy them!

```sh
git checkout master                   # switch to the master branch locally
git pull                              # get the latest changes from GitHub
pip install -r requirements/all.txt   # update installed dependencies
pip install -e .                      # update installed PyBioPharma
```

You will need to restart the kernel in any running Jupyter notebook for it to
use the new version.


## Merging new changes from the master (main) branch into your own

First, get the latest version of 'master' from GitHub:

```sh
git checkout master
git pull
```

Then change back to your own branch and merge the new version of master:

```sh
git checkout jonathan/experimental   # Or whatever your branch is called
git merge master
```

You may find that git refuses to merge because some of the new changes conflict
with your modifications. If this happens, you will need to decide how to
combine things. See http://swcarpentry.github.io/git-novice/09-conflict/ for
more guidance.

You will reduce the chances of conflicts happening if you make copies of the
demo notebooks before changing them. Similarly if you are working on a
different model, making new files with new process step classes is sensible.


## Sharing your changes with others

Once you have pushed your branch to GitHub, you can create a 'pull request' to
ask a project maintainer to merge features into the main version of
PyBioPharma. See [GitHub's pull request documentation](PR) for more on how to
do this.

[PR]: https://help.github.com/articles/about-pull-requests/
