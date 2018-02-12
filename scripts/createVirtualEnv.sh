#!/usr/bin/env bash

gitRoot=$(git rev-parse --show-cdup)
interpreter="/usr/bin/python3.6"
envPath="${gitRoot}virtualenv"
envExec="${envPath}/bin/python"
requirementsFile="${gitRoot}requirements.txt"

sudo apt install virtualenv python3-tk python3.6
virtualenv -p ${interpreter} ${envPath}
${envExec} -m pip install --exists-action i -r ${requirementsFile}
