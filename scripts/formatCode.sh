#!/usr/bin/env bash

gitRoot=$(git rev-parse --show-cdup)
pythonSrcDir="${gitRoot}python/src"

find ${pythonSrcDir} | grep -F .py | grep -v -F .pyc | xargs autopep8 -v -v -i --max-line-length 80
