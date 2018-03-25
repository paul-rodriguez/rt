#!/usr/bin/env bash

# Use this script to run tests.
# Arguments given to this script are passed to pytest.
# By default, all tests not marked as "slow" are run.
# To run slow tests, call the script with `-m "slow"` (or change this script to
# match your needs).

set -e

gitRoot=$(git rev-parse --show-cdup)
pytest=${gitRoot}virtualenv/bin/pytest
testDir=${gitRoot}src/tests

${pytest} ${testDir} -v -m "not slow" "$@"
