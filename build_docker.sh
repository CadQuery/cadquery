#!/bin/bash
set -e

#builds and tests the docker image
docker build -t dcowden/cadquery .

# set up tests
CQ_TEST_DIR=/tmp/cq_docker-test
mkdir -p $CQ_TEST_DIR
rm -rf $CQ_TEST_DIR/*.*
cp examples/FreeCAD/Ex001_Simple_Block.py $CQ_TEST_DIR


fail_test(  ){
   "Test Failed."
}

echo "Running Tests..."
echo "No arguments prints documentation..."
docker run  dcowden/cadquery | grep "CadQuery Docker Image" || fail_test
echo "OK"

echo "Std in and stdout..."
cat $CQ_TEST_DIR/Ex001_Simple_Block.py | docker run -i  dcowden/cadquery build --in_spec stdin --out_spec stdout | grep "ISO-10303-21" || fail_test
echo "OK"

echo "Mount a directory and produce output..."
docker run -i -v $CQ_TEST_DIR:/home/cq  dcowden/cadquery build --in_spec Ex001_Simple_Block.py --format STEP
ls $CQ_TEST_DIR | grep "cqobject-1.STEP" || fail_test
echo "OK"

echo "Future Server EntryPoint"
docker run -i dcowden/cadquery runserver | grep "Future CadQuery Server" || fail_test
echo "OK"
