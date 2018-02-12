# Compatibility

Tested on Ubuntu 16.04 and 16.10.
Other OS are supported but the creation of the virtual environment is not
automated.

# Installation

Run `scripts/createVirtualEnv.sh` to create a Python 3 virtual environment with
all required dependencies.
The virtual environment is created in the directory containing this readme.

# Usage

Useful entry point scripts are in the `src/` folder.

To execute your own scripts, run them with the `python` interpreter found in
`virtualenv/bin/` after installation and make sure the modules in the `/src`
directory are visible by python (the easiest way is to execute your command in
the `/src` directory).

The `crpd` and `dualpriority` packages contain a number of modules that allow
to build task sets and run simulations on them with a couple of lines of python
code.
Read the tests in the `/tests` directory to have examples of how to use these
modules.

## Tests

To run tests, invoke the `pytest` executable found in `virtualenv/bin/` with
the `src/` folder as current directory (or pass it as argument to pytest).
Pytest supports various options for test collection (such as running a test file
or function in particular).
You can copy, extend or modify existing test files to run your own simulations,
pytest doesn't need to be configured to find your tests.

## dpsearch.py

This script searches for systems that are not schedulable with the RML
(RM Laxity) dual-priority assignment policy.
