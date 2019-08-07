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

This image is not [CQGI-compliant](https://cadquery.readthedocs.io/en/latest/cqgi.html) yet.
You must use CadQuery as a library for now.

## Usage

### Using stdin

```bash
echo "import cadquery; print(cadquery.Workplane('XY').box(1,2,3).toSvg())" > cadquery_script.py
cat cadquery_script.py | docker run --rm -i roipoussiere/cadquery2 > 3d_model.svg
```

### Using volumes

**The following options are planned but are not implemented for now, and syntax may change.**

If your CadQuery project depends on many files, you may be interested by putting them in a volume:

```bash
mkdir my_input_files
echo "<some CadQuery code>" > ./my_input_files/a.py
echo "<some CadQuery code that depends on a.py>" > ./my_input_files/b.py
docker run roipoussiere/cadquery2 --rm -v $(pwd)/my_input_files:/cq-input/:ro a.py > 3d_model.svg
```

If your project is going to generate several files, you can also export your files in an other volume:

```bash
mkdir my_input_files
echo "show_object(cq.Workplane('XY').box(1,2,3))" > ./my_input_files/a.py
echo "show_object(cq.Workplane('XY').box(2,3,4))" > ./my_input_files/b.py
docker run roipoussiere/cadquery2 --rm -v $(pwd)/my_input_files:/cq-input/:ro -v $(pwd)/my_output_files:/cq-output a.py,b.py
```

## Customizing this image

Although this Docker image should work out of the box, you may be interested to customize it by giving docker build arguments:
- `OCE_VERSION`: oce version, that can be a commit sha, a branch name or a release name (default: `master`);
- `PYTHONOCC_CORE_VERSION`: pythonocc-core version, that can be a commit sha, a branch name or a release name (default: `master`);
- `CADQUERY_VERSION`: CadQuery version, that can be a commit sha, a branch name or a release name (default: `master`).

Example usage: `docker build --build-arg OCE_VERSION=OCE-0.18.1 .` ([read more about build args](https://docs.docker.com/engine/reference/commandline/build/#set-build-time-variables---build-arg))
