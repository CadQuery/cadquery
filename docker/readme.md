# CadQuery2 - docker

A Dockerfile for [CadQuery2](https://github.com/CadQuery/cadquery).

**This is a work in progress.**

## Introduction

This Docker executable takes any CadQuery2 Python code, and outputs its 3d model in STL, STEP, AMF, SVG or TJS.

This can be useful for:
- get a quick overview of CadQuery2 scripting;
- get the STL file of a cadQuery code found somewhere;
- generate a documentation that includes some images of a 3d-model;
- use it in a Continuous Integration workflow in various ways, such as publishing up-to-date STLs of a CadQuery project.

## Writing a script

~~This container is [CQGI-compliant](https://cadquery.readthedocs.io/en/latest/cqgi.html):~~

> CQGI compliant containers provide an execution environment for scripts. The environment includes:
> 
> - the cadquery library is automatically imported as ‘cq’.
> - the cadquery.cqgi.ScriptCallback.show_object() method is defined that should be used to export a shape to the execution environment
> - the cadquery.cqgi.ScriptCallBack.debug() method is defined, which can be used by scripts to debug model output during execution.

## Usage

### Using command parameter

Just put your Python code as a parameter of the `docker run` CLI command.

```bash
docker run roipoussiere/cadquery2 'show_object(cq.Workplane('XY').box(1,2,3))'
```

```bash
echo 'show_object(cq.Workplane('XY').box(1,2,3))' > myCadQuery2Script.py
cat myCadQuery2Script.py | docker run roipoussiere/cadquery2 -a stdin
```

### Using volumes

~~If your CadQuery project depends on many files, you may be interested by putting them in a volume:~~

```bash
mkdir my_input_files
echo 'show_object(cq.Workplane('XY').box(1,2,3))' > ./my_input_files/1.py
echo 'show_object(cq.Workplane('XY').box(2,3,4))' > ./my_input_files/2.py
docker run roipoussiere/cadquery2 -v $(pwd)/my_input_files:/cq-input/:ro
```

~~If your project is going to generate several files, you can also export your files in an other volume:~~

```bash
mkdir my_input_files
echo 'show_object(cq.Workplane('XY').box(1,2,3))' > ./my_input_files/1.py
echo 'show_object(cq.Workplane('XY').box(2,3,4))' > ./my_input_files/2.py
docker run roipoussiere/cadquery2 -v $(pwd)/my_input_files:/cq-input/:ro -v $(pwd)/my_output_files:/cq-output
```
