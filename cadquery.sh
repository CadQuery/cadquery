#!/bin/bash

STDIN=$(cat)

if [ -z "$STDIN" ]; then
   echo "*** CadQuery2 Docker Image ***"
   echo ""
   echo "Usage: docker run roipoussiere/cadquery2 [options]"
   echo "Examples:"
   echo "- read a CadQuery script from stdin, write output 3d model svg to stdout:"
   echo "    echo \"import cadquery; print(cadquery.Workplane('XY').box(1,2,3).toSvg())\" > cadquery_script.py"
   echo "    cat cadquery_script.py | docker run --rm -i roipoussiere/cadquery2 > 3d_model.svg"
   exit 1
else
   exec python3 -c "$STDIN"
fi;
