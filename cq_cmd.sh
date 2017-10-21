#!/bin/bash
# NOTE
# the -u (unbuffered flag) in the below is very important
# without it, the FreeCAD libraries somehow manage to get some stdout
# junking up output when stdout is used.
# this is the script we use
# to select between running a build server
# and a command line job runner
if [ -z "$1" ]; then
   echo "Usage: docker run cadquery build|server [options]"
   exit(1)
fi;
if [ "$1" == "build"]; then
   exec python -u /opt/cadquery/cq_cmd.py "$@"
fi;
if [ "$1" == "runserver"]; then
   exec python -u /opt/cadquery/cq_server.py "$@"
fi;
