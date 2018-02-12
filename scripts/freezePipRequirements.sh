#!/usr/bin/env bash

gitRoot=$(git rev-parse --show-cdup)
pythonExec=${gitRoot}python/virtualenv/bin/python3.6
requirementsFile=${gitRoot}python/requirements.txt

${pythonExec} -m pip freeze > ${requirementsFile}
