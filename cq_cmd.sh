#!/bin/bash
if [ -z "$1" ]; then
   python cq_cmd.py --help
else
   python cq_cmd.py "$@"
fi;
