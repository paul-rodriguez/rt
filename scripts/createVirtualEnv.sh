#!/usr/bin/env bash

set -e

gitRoot=$(git rev-parse --show-cdup)
interpreter="/usr/bin/python3.6"
envPath="${gitRoot}virtualenv"
envExec="${envPath}/bin/python"
requirementsFile="${gitRoot}requirements.txt"

pypyFileName="pypy3.5-7.0.0-linux_x86_64-portable"
pypyUrl="https://bitbucket.org/squeaky/portable-pypy/downloads/${pypyFileName}.tar.bz2"
pypyDir="${gitRoot}pypy/"
pypyVirtualenv="${pypyDir}/bin/virtualenv-pypy"

wget -N ${pypyUrl}
tar -xf "${pypyFileName}.tar.bz2"
mkdir -p ${pypyDir}
mv -n ${pypyFileName}/* ${pypyDir}
${pypyVirtualenv} --clear ${envPath}
${envExec} -m pip install --exists-action i -r ${requirementsFile}
rm -rf "${pypyFileName}"
