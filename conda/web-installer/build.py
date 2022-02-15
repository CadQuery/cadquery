import sys
import os
import subprocess
from jinja2 import Environment, select_autoescape, FileSystemLoader


def usage():
    print("Web installer build script")
    print("build.py <installer version> <tag version>")
    print(
        "The installer verison is the version number used within the conda constructor script"
    )
    print("The tag verison is the version of cadquery that will be pulled from github")


def write_file(destpath, contents):
    with open(destpath, "w") as destfile:
        destfile.write(contents)


def run_cmd(cmdarray, workingdir, captureout=False):
    stdout = stderr = None
    if captureout:
        stdout = stderr = subprocess.PIPE
    proc = subprocess.Popen(
        cmdarray, cwd=workingdir, stdout=stdout, stderr=stderr, universal_newlines=True
    )
    proc_out, proc_err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError("Failure to run command")
    return stdout, stderr


def generate_templates(installer_version, tag_version):
    print("Generating Scripts")
    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())

    template = env.get_template("construct.yaml.jinja2")
    output = template.render(installer_version=installer_version)
    write_file("construct.yaml", output)

    template = env.get_template("post-install.bat.jinja2")
    output = template.render(tag_version=tag_version)
    write_file("post-install.bat", output)

    template = env.get_template("post-install.sh.jinja2")
    output = template.render(tag_version=tag_version)
    write_file("post-install.sh", output)


def run_constructor():
    print("Running constructor")
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    builddir = os.path.join(scriptdir, "build")
    if not os.path.exists(builddir):
        os.makedirs(builddir)
    run_cmd(["constructor", scriptdir], builddir)


def main():
    if len(sys.argv) < 2:
        usage()
        return
    installer_version = sys.argv[1]
    tag_version = sys.argv[2]
    generate_templates(installer_version, tag_version)
    run_constructor()


main()
