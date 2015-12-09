"""

The CadQuery Container Environment.
Provides classes and tools for executing CadQuery scripts
"""
import ast
import traceback
import re
import time

CQSCRIPT = "<cqscript>"


class CQModel(object):
    """
    Object that provides a nice interface to a cq script that
    is following the cce model
    """

    def __init__(self, script_source):
        self.metadata = ScriptMetadata()
        self.astTree = ast.parse(script_source, CQSCRIPT)

        ConstantAssignmentFinder(self.metadata).visit(self.astTree)

        # TODO: pick up other scirpt metadata:
        # describe
        # pick up validation methods

    def validate(self, params):
        raise NotImplementedError("not yet implemented")

    def build(self, params=None):
        """

        :param params: dictionary of parameter values to build with
        :return:
        """
        if not params:
            params = {}

        self.set_param_values(params)
        collector = BuildObjectCollector()
        env = EnvironmentBuilder().with_real_builtins() \
            .add_entry("build_object", collector.build_object).build()

        start = time.clock()
        result = BuildResult()

        try:
            c = compile(self.astTree, CQSCRIPT, 'exec')
            exec (c, env)
            if collector.hasResults():
                result.set_success_result(collector.outputObjects)
            else:
                raise ValueError("Script did not call build_object-- no output available.")
        except Exception, ex:
            result.set_failure_result(ex)

        end = time.clock()
        result.buildTime = end - start
        return result

    def set_param_values(self, params):
        model_parameters = self.metadata.parameters

        for k, v in params.iteritems():
            if k not in model_parameters:
                raise InvalidParameterError("Cannot set value '%s': not a parameter of the model." % k)

            p = model_parameters[k]
            p.set_value(v)


class BuildResult(object):
    def __init__(self):
        self.buildTime = None
        self.results = []
        self.success = False
        self.exception = None

    def set_failure_result(self, ex):
        self.exception = ex
        self.success = False

    def set_success_result(self, results):
        self.results = results
        self.success = True


class ScriptMetadata(object):
    def __init__(self):
        self.parameters = {}

    def add_script_parameter(self, p):
        self.parameters[p.name] = p


class ParameterType(object):
    pass


class NumberParameterType(ParameterType):
    pass


class StringParameterType(ParameterType):
    pass


class BooleanParameterType(ParameterType):
    pass


class InputParameter:
    def __init__(self):
        self.name = None
        self.shortDesc = None
        self.varType = None
        self.validValues = []
        self.default_value = None
        self.ast_node = None

    @staticmethod
    def create(ast_node, var_name, var_type, default_value, valid_values=None, short_desc=None):

        if valid_values is None:
            valid_values = []

        p = InputParameter()
        p.ast_node = ast_node
        p.default_value = default_value
        p.name = var_name
        if short_desc is None:
            p.shortDesc = var_name
        else:
            p.shortDesc = short_desc
        p.varType = var_type
        p.validValues = valid_values
        return p

    def set_value(self, new_value):

        if len(self.validValues) > 0 and not new_value in self.validValues:
            raise InvalidParameterError(
                "Cannot set value '{0:s}' for parameter '{1:s}': not a valid value. Valid values are {2:s} "
                    .format( str(new_value), self.name, str(self.validValues)))

        if self.varType == NumberParameterType:
            try:
                f = float(new_value)
                self.ast_node.n = f
            except ValueError:
                raise InvalidParameterError(
                    "Cannot set value '{0:s}' for parameter '{1:s}': parameter must be numeric."
                        .format(str(new_value), self.name))

        elif self.varType == StringParameterType:
            self.ast_node.s = str(new_value)
        elif self.varType == BooleanParameterType:
            if new_value:
                self.ast_node.value.id = 'True'
            else:
                self.ast_node.value.id = 'False'
        else:
            raise ValueError("Unknown Type of var: ", str(self.varType))

    def __str__(self):
        return "InputParameter: {name=%s, type=%s, defaultValue=%s" % (
            self.name, str(self.varType), str(self.default_value))


class BuildObjectCollector(object):
    """
    Allows a script to provide output objects
    """

    def __init__(self):
        self.outputObjects = []

    def build_object(self, shape):
        self.outputObjects.append(shape)

    def hasResults(self):
        return len(self.outputObjects) > 0


class ScriptExecutor(object):
    """
    executes a script in a given environment.
    """

    def __init__(self, environment, astTree):

        try:
            exec (astTree) in environment
        except Exception, ex:

            # an error here means there was a problem compiling the script
            # try to figure out what line the error was on
            traceback.print_exc()
            formatted_lines = traceback.format_exc().splitlines()
            line_text = ""
            for f in formatted_lines:
                if f.find(CQSCRIPT) > -1:
                    m = re.search("line\\s+(\\d+)", f, re.IGNORECASE)
                    if m and m.group(1):
                        line_text = m.group(1)
                    else:
                        line_text = 0

            sse = ScriptExecutionError()
            sse.line = int(line_text)
            sse.message = str(ex)
            raise sse


class InvalidParameterError(Exception):
    pass


class ScriptExecutionError(Exception):
    """
        Represents a script syntax error.
        Useful for helping clients pinpoint issues with the script
        interactively
    """

    def __init__(self, line=None, message=None):
        if line is None:
            self.line = 0
        else:
            self.line = line

        if message is None:
            self.message = "Unknown Script Error"
        else:
            self.message = message

    def full_message(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "ScriptError [Line %s]: %s" % (self.line, self.message)


class EnvironmentBuilder(object):
    def __init__(self):
        self.env = {}

    def with_real_builtins(self):
        return self.with_builtins(__builtins__)

    def with_builtins(self, env_dict):
        self.env['__builtins__'] = env_dict
        return self

    def add_entry(self, name, value):
        self.env[name] = value
        return self

    def build(self):
        return self.env


class ConstantAssignmentFinder(ast.NodeTransformer):
    """
    Visits a parse tree, and adds script parameters to the cqModel
    """

    def __init__(self, cq_model):
        self.cqModel = cq_model

    def handle_assignment(self, var_name, value_node):
        if type(value_node) == ast.Num:
            self.cqModel.add_script_parameter(
                InputParameter.create(value_node, var_name, NumberParameterType, value_node.n))
        elif type(value_node) == ast.Str:
            self.cqModel.add_script_parameter(
                InputParameter.create(value_node, var_name, StringParameterType, value_node.s))
        elif type(value_node == ast.Name):
            if value_node.value.Id == 'True':
                self.cqModel.add_script_parameter(
                    InputParameter.create(value_node, var_name, BooleanParameterType, True))
            elif value_node.value.Id == 'False':
                self.cqModel.add_script_parameter(
                    InputParameter.create(value_node, var_name, BooleanParameterType, True))

    def visit_Assign(self, node):
        left_side = node.targets[0]
        if type(node.value) in [ast.Num, ast.Str, ast.Name]:
            self.handle_assignment(left_side.id, node.value)
        elif type(node.value) == ast.Tuple:
            # we have a multi-value assignment
            for n, v in zip(left_side.elts, node.value.elts):
                self.handle_assignment(n.id, v)
        return node
