import re


def process_docstring_multimethod(app, what, name, obj, options, lines):
    """multimethod docstring customization

    Remove extraneous signatures and combine docstrings if docstring also defined
    in registered method.
    """

    # get list of multimethod names identified during signature formatting
    from ._dynamic._signatures import MM_NAMES

    if name not in MM_NAMES or what not in ("method", "function"):
        return

    fname = name.split(".")[-1]
    patsig = re.compile(rf"\s*({fname})\(.*\).*")

    indent = -1
    sig = False
    for i in range(0, len(lines)):
        line = lines[i]
        if indent < 0:
            # indent of first signature
            indent = len(line) - len(line.lstrip())
            lines[i] = line[indent:]
        elif sig:
            # indent of next signature (skip empty lines)
            if line.strip():
                indent = len(line) - len(line.lstrip())
                lines[i] = line[indent:]
                sig = False
            else:
                lines[i] = ""
        elif patsig.match(line):
            # signature line
            sig = True
            lines[i] = ""
        else:
            lines[i] = line[indent:]
