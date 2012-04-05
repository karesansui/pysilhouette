#!/bin/bash
#
# epydoc.sh - The command to generate python API documentation pysilhouette
#
# require rpm - python-epydoc, graphviz-doc, graphviz, graphviz-devel, graphviz-graphs, graphviz-gd
#

name=pysilhouette
PATH=${PATH}:/usr/bin
export PYTHONPATH=${PYTHONPATH}:/usr/lib/python:/usr/lib/python2.6:/usr/lib/python2.6/site-packages

script_dir=`dirname $0`
pushd $script_dir >/dev/null 2>&1
# shell directory.
script_dir=`pwd`
popd >/dev/null 2>&1

epydoc_config=${script_dir}/../doc/epydoc.cfg


target=/var/www/html/${name}-doc

if [ -e ${target} ]; then
  rm -fr ${target}
fi
mkdir -p ${target}

epydoc --config ${epydoc_config}
