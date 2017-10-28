#
# cadquery command line interface
# usage: cq_cmd  [-h] [--param-file inputfile ] [--format STEP|STL ] [--output filename] filename
# if input file contains multiple inputs, multiple outputs are created
# if no input filename is provided, stdin is read instead
# if no output filename is provided, output goes to stdout
# default output format is STEP
#
from __future__ import print_function
import sys,os







from cadquery import cqgi,exporters
import argparse
import os.path
import json
import tempfile

class FilepathShapeWriter(object):
    #a shape writer that writes a new file in a directory for each object
    def __init__(self,file_pattern, shape_format):
        self.shape_format=shape_format
        self.file_pattern=file_pattern
        self.counter = 1

    def _compute_file_name(self):
        return self.file_pattern % ({ "counter": self.counter,"format": self.shape_format } )

    def write_shapes(self,shape_list):
        for result in shape_list:
            shape = result.shape
            file_name = self._compute_file_name()
            info("Writing %s Output to '%s'" % (self.shape_format, file_name))
            s = open(file_name,'w')
            exporters.exportShape(shape,self.shape_format,s)
            s.flush()
            s.close()

class StdoutShapeWriter(object):
    #has extra code to prevent freecad crap from junking up stdout
    def __init__(self,shape_format ):
        self.shape_format = shape_format

    def write_shapes(self,shape_list):
        #f = open('/tmp/cqtemp','w')
        #with suppress_stdout_stderr():
        exporters.exportShape(shape_list[0].shape,self.shape_format,sys.stdout)
        #f.flush()
        #f.close()
        #f = open('/tmp/cqtemp')
        #sys.stdout.write(f.read())


def create_shape_writer(out_spec,shape_format):
    if out_spec == 'stdout':
        return StdoutShapeWriter(shape_format)
    else:
        return FilepathShapeWriter(out_spec,shape_format)

class ErrorCodes(object):
    SCRIPT_ERROR=2
    UNKNOWN_ERROR=3
    INVALID_OUTPUT_DESTINATION=4
    INVALID_OUTPUT_FORMAT=5
    INVALID_INPUT=6
    MULTIPLE_RESULTS=7

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def error(msg,exit_code=1):
    eprint("ERROR %d: %s" %( exit_code,  msg))
    sys.exit(exit_code)

def warning(msg):
    eprint("WARNING: %s" % msg)

def info(msg):
    eprint("INFO: %s" % msg)

def read_file_as_string(file_name):
    if os.path.isfile(file_name):
        f = open(file_name)
        s = f.read()
        f.close()
        return s
    else:
        return None

class ParameterHandler(object):
    def __init__(self):
        self.params = {}

    def apply_file(self,file_spec):
        if file_spec is not None:
            p = read_file_as_string(file_spec)
            if p is not None:
                d = json.loads(p)
                self.params.update(d)

    def apply_string(self,param_string):
        if param_string is not None:
            r = json.loads(param_string)
            self.params.update(r)

    def get(self):
        return self.params

def read_input_script(file_name):
    if file_name != "stdin":
        s = read_file_as_string(file_name)
        if s is None:
            error("%s does not appear to be a readable file." % file_name,ErrorCodes.INVALID_INPUT)
        else:
            return s
    else:
        s = sys.stdin.read()
        return s

def check_input_format(input_format):
    valid_types = [exporters.ExportTypes.TJS,exporters.ExportTypes.AMF,
        exporters.ExportTypes.STEP,exporters.ExportTypes.STL,exporters.ExportTypes.TJS ]
    if input_format not in valid_types:
        error("Invalid Input format '%s'. Valid values: %s" % ( input_format, str(valid_types)) ,
        ErrorCodes.INVALID_OUTPUT_FORMAT)


def describe_parameters(user_params, script_params):
    if len(script_params)> 0:
        parameter_names = ",".join(script_params.keys())
        info("This script provides parameters %s, which can be customized at build time." % parameter_names)
    else:
        info("This script provides no customizable build parameters.")
    if len(user_params) > 0:
        info("User Supplied Parameter Values ( Override Model Defaults):")
        for k,v in user_params.iteritems():
            info("\tParameter: %s=%s" % (k,v))
    else:
        info("The script will run with default variable values")
        info("use --param_file to provide a json file that contains values to override the defaults")

def run(args):

    info("Reading from file '%s'" % args.in_spec)
    input_script = read_input_script(args.in_spec)
    script_name = 'stdin' if args.in_spec is None else args.in_spec
    cq_model = cqgi.parse(input_script)
    info("Parsed Script '%s'." % script_name)

    param_handler = ParameterHandler()
    param_handler.apply_file(args.param_file)
    param_handler.apply_string(args.params)
    user_params = param_handler.get()
    describe_parameters(user_params,cq_model.metadata.parameters)

    check_input_format(args.format)

    build_result = cq_model.build(build_parameters=user_params)

    info("Output Format is '%s'. Use --output-format to change it." % args.format)
    info("Output Path is '%s'. Use --out_spec to change it." % args.out_spec)

    if build_result.success:
        result_list = build_result.results
        info("Script Generated %d result Objects" % len(result_list))
        shape_writer = create_shape_writer(args.out_spec,args.format)
        shape_writer.write_shapes(result_list)
    else:
        error("Script Error: '%s'" % build_result.exception,ErrorCodes.SCRIPT_ERROR)

if __name__=='__main__':

    desc="""
CQ CMD. Runs a cadquery python file, and produces a 3d object.
A script can be provided as a file or as standard input.
Each object created by the script is written the supplied output directory.
    """
    filename_pattern_help="""
Filename pattern to use when creating output files.
The sequential file number and the format are available.
Default: cqobject-%%(counter)d.%%(format)s
Use stdout to write to stdout ( can't be used for multiple results though)
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--format", action="store",default="STEP",help="Output Object format (TJS|STEP|STL|SVG)")
    parser.add_argument("--param_file", action="store",help="Parameter Values File, in JSON format")
    parser.add_argument("--params",action="store", help="JSON encoded parameter values. They override values provided in param_file")
    parser.add_argument("--in_spec", action="store", required=True, help="Input File path. Use stdin to read standard in")
    parser.add_argument("--out_spec", action="store",default="./cqobject-%(counter)d.%(format)s",help=filename_pattern_help)
    args = parser.parse_args()
    run(args)
