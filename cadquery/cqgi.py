"""

The CadQuery Container Environment.
Provides classes and tools for executing CadQuery scripts
"""
import ast
import traceback
import re
import time
import cadquery

CQSCRIPT = "<cqscript>"


def execute(script_source, build_parameters=None):
    """
    Executes the provided model, using the specified variables.

    If you would prefer to access the underlying model without building it,
    for example, to inspect its available parameters, construct a CQModel object.

    :param script_source: the script to run. Must be a valid cadquery script
    :param build_parameters: a dictionary of variables. The variables must be
       assignable to the underlying variable type.
    :raises: Nothing. If there is an exception, it will be on the exception property of the result.
       This is the interface so that we can return other information onthe result, such as the build time
    :return: a BuildResult object, which includes the status of the result, and either
       a resulting shape or an exception
    """
    model = CQModel(script_source)
    return model.build(build_parameters)


class CQModel(object):
    """
    Object that provides a nice interface to a cq script that
    is following the cce model
    """

    def __init__(self, script_source):
        self.metadata = ScriptMetadata()
        self.ast_tree = ast.parse(script_source, CQSCRIPT)

        ConstantAssignmentFinder(self.metadata).visit(self.ast_tree)

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

        start = time.clock()
        result = BuildResult()

        try:
            self.set_param_values(params)
            collector = BuildObjectCollector()
            env = EnvironmentBuilder().with_real_builtins().with_cadquery_objects() \
                .add_entry("build_object", collector.build_object).build()

            c = compile(self.ast_tree, CQSCRIPT, 'exec')
            exec (c, env)
            if collector.has_results():
                result.set_success_result(collector.outputObjects)
            else:
                raise NoOutputError("Script did not call build_object-- no output available.")
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
        self.first_result = None
        self.success = False
        self.exception = None

    def set_failure_result(self, ex):
        self.exception = ex
        self.success = False

    def set_success_result(self, results):
        self.results = results
        self.first_result = self.results[0]
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
        self.valid_values = []
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
        p.valid_values = valid_values
        return p

    def set_value(self, new_value):

        if len(self.valid_values) > 0 and new_value not in self.valid_values:
            raise InvalidParameterError(
                "Cannot set value '{0:s}' for parameter '{1:s}': not a valid value. Valid values are {2:s} "
                    .format(str(new_value), self.name, str(self.valid_values)))

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

    def has_results(self):
        return len(self.outputObjects) > 0


class ScriptExecutor(object):
    """
    executes a script in a given environment.
    """

    def __init__(self, environment, ast_tree):

        try:
            exec ast_tree in environment
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


class NoOutputError(Exception):
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

    def with_cadquery_objects(self):
        self.env['cadquery'] = cadquery
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
