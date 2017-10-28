#!/bin/bash
# NOTE
# the -u (unbuffered flag) in the below is very important
# without it, the FreeCAD libraries somehow manage to get some stdout
# junking up output when stdout is used.
# this is the script we use
# to select between running a build server
# and a command line job runner
if [ -z "$1" ]; then
   echo "************************"
   echo "CadQuery Docker Image"
   echo "************************"
   echo "Usage: docker run cadquery build [options]"
   echo "Examples:"
   echo " Read a model from stdin, write output to stdout"
   echo ""
   echo "    cat cadquery_script.py | sudo docker run -i dcowden/cadquery:latest --in_spec stdin --out_spec stdout > my_object.STEP"
   echo " "
   echo " Mount a directory, and write results into the local directory"
   echo ""
   echo "    sudo docker run -i dcowden/cadquery:latest --in_spec my_script.py"
   echo ""
   exec python -u /opt/cadquery/cq_cmd.py -h
   exit 1
fi;
if [ "$1" == "build" ]; then
   exec python -u /opt/cadquery/cq_cmd.py "${@:2}"
fi;
if [ "$1" == "runserver" ]; then
  echo "Future CadQuery Server"
  exit 1
   #exec python -u /opt/cadquery/cq_server.py "${@:2}"
fi;
