#!/usr/bin/env bash

set -e

gitRoot=$(git rev-parse --show-cdup)
interpreter="/usr/bin/python3.6"
envPath="${gitRoot}virtualenv"
envExec="${envPath}/bin/python"
requirementsFile="${gitRoot}requirements.txt"

pypyUrl="https://bitbucket.org/squeaky/portable-pypy/downloads/pypy3.5-5.10.1-linux_x86_64-portable.tar.bz2"
pypyDir="${gitRoot}pypy/"
pypyVirtualenv="${pypyDir}/bin/virtualenv-pypy"

wget -N ${pypyUrl}
tar -xf pypy3.5-5.10.1-linux_x86_64-portable.tar.bz2
mkdir -p ${pypyDir}
mv -n pypy3.5-5.10.1-linux_x86_64-portable/* ${pypyDir}
${pypyVirtualenv} --clear ${envPath}
${envExec} -m pip install --exists-action i -r ${requirementsFile}
rm -rf pypy3.5-5.10.1-linux_x86_64-portable
