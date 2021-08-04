#!/bin/sh
(cd doc && sphinx-build -b html . ../target/docs)
