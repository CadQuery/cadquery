#!/bin/bash
if [ -z "$1" ]; then
   python /opt/cadquery/cq_cmd.py --help
else
   python /opt/cadquery/cq_cmd.py "$@"
fi;
