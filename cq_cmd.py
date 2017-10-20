#
# cadquery command line interface
# usage: cq_cmd  [-h] [--param-file inputfile ] [--format STEP|STL ] [--output filename] filename
# if input file contains multiple inputs, multiple outputs are created
# if no input filename is provided, stdin is read instead
# if no output filename is provided, output goes to stdout
# default output format is STEP
#
from __future__ import print_function
from cadquery import cqgi,exporters
import argparse
import sys
import os.path
import json


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

def make_output_filename(counter,format_pattern, shape_format):
    return format_pattern % ({ "counter": counter,"format": shape_format } )

def read_param_file(file_name):
    if file_name is not None:
        p = read_file_as_string(file_name)
        if p is not None:
            info("Build Parameters: %s" % str(p))
            return json.parse(p)

    return {}
def read_file_as_string(file_name):
    if os.path.isfile(file_name):
        f = open(file_name)
        s = f.read()
        f.close()
        return s
    else:
        return None

def read_input_script(file_name):
    if file_name:
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

def export_to_file(filename, shape, shape_format):
    info("Writing %s Output to '%s'" % (shape_format, filename))
    s = open(filename,'w')
    exporters.exportShape(shape,shape_format,s)
    s.flush()
    s.close()

def output_single_result(user_output_filename, shape_format,shape_result,file_format_pattern):
    output_filename = None
    if user_output_filename is None:
        output_filename = make_output_filename(1,file_format_pattern,shape_format)
    elif os.path.isfile(user_output_filename):
        output_filename = user_output_filename
    elif os.path.isdir(user_output_filename):
        output_filename = os.path.join(user_output_filename, make_output_filename(1,file_format_pattern,shape_format))
    else:
        error("Can't write to destination %s'" % user_output_filename, ErrorCodes.INVALID_OUTPUT_DESTINATION)
    export_to_file(output_filename,shape_result.shape,shape_format)

def output_multiple_results(output_filename,shape_format, result_list,file_format_pattern):

    if output_filename is None or not os.path.isdir(output_filename):
        info("No output destination provided. using current directory.")
        output_filename = "."
    counter = 1
    for shape_result in result_list:
        fname = make_output_filename(counter,file_format_pattern,shape_format)
        outfile_name = os.path.join(output_filename, fname)
        export_to_file(outfile_name,shape_result.shape,shape_format)
        counter += 1

def process_parameters(script_param_file, script_params):
    if len(script_params)> 0:
        parameter_names = ",".join(script_params.keys())
        info("This script provides parameters %s, which can be customized at build time." % parameter_names)
    else:
        info("This script provides no customizable build parameters.")

    params = read_param_file(script_param_file)
    if len(params) > 0:
        info("User Supplied Parameter Values ( Override Model Defaults):")
        info(str(params))
    else:
        info("The script will run with default variable values")
        info("use --param_file to provide a json file that contains values to override the defaults")
    return params

def run(args):


    input_script = read_input_script(args.in_file)
    script_name = 'stdin' if args.in_file is None else args.in_file
    cq_model = cqgi.parse(input_script)
    info("Parsed Script '%s'." % script_name)

    params = process_parameters(args.param_file,cq_model.metadata.parameters)

    output_format = 'STEP'
    if args.output_format:
        check_input_format(args.output_format)
        output_format = args.output_format

    info("Output Format is '%s'. Use --output-format to change it." % output_format)
    info("Output Directory is '%s'. Use --out_dir to change it." % args.out_dir)
    info("Output File Pattern is '%s'. Use --filename_pattern to change it." % args.filename_pattern)

    build_result = cq_model.build(build_parameters=params)
    if build_result.success:
        result_list = build_result.results
        info("Script Generated %d result Objects" % len(result_list))
        if len(result_list) > 1:
            output_multiple_results(args.out_dir, output_format, result_list,args.filename_pattern)
        else:
            output_single_result(args.out_dir,output_format,result_list[0],args.filename_pattern)
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
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--output_format", action="store",help="Output Object format (TJS|STEP|STL|SVG)")
    parser.add_argument("--param_file", action="store",help="Parameter Values File, in JSON format")
    parser.add_argument("--in_file", action="store", help="Input File path. If omitted, read stdin")
    parser.add_argument("--filename_pattern",action="store", default="cqobject-%(counter)d.%(format)s",help=filename_pattern_help)
    parser.add_argument("--out_dir", action="store", help="Output File Directory. If omitted, current work directory is used")
    args = parser.parse_args()

    run(args)
