"""

The CadQuery Container Environment.
Provides classes and tools for executing CadQuery scripts
"""
import ast
import traceback
import re
import time

CQSCRIPT= "<cqscript>"
BUILD_OBJECT_COLLECTOR = "__boc__"

class CQModel(object):
    """
    Object that provides a nice interface to a cq script that
    is following the cce model
    """
    def __init__(self,scriptSource):
        self.metadata = ScriptMetadata()
        self.astTree = ast.parse(scriptSource,CQSCRIPT)

        ConstantAssignmentFinder(self.metadata).visit(self.astTree)

        #TODO: pick up other scirpt metadata:
        # describe
        # pick up validation methods

    def validate(self,params):
        raise NotImplementedError("not yet implemented")

    def build(self,params):
        """

        :param params: dictionary of parameter values to build with
        :return:
        """
        self.setParamValues(params)
        collector = BuildObjectCollector()
        env = EnvironmentBuilder().withRealBuiltins() \
            .addEntry("build_object",collector.build_object).build()

        start = time.clock()
        result = BuildResult()


        c = compile(self.astTree,CQSCRIPT,'exec')
        exec (c,env)
        if collector.hasResults():
            result.setSuccessResult(collector.outputObjects)
        else:
            raise ValueError("Script did not call build_object-- no output available.")
        #except Exception,ex:

        #    result.setFailureResult(ex)

        end = time.clock()
        result.buildTime = end - start
        return result

    def setParamValues(self,params):
        modelParameters = self.metadata.parameters

        for k,v in params.iteritems():
            if not modelParameters.has_key(k):
                raise ValueError("Cannot set value '%s', it is not a parameter of the model." % k)

            p = modelParameters[k]
            p.setValue(v)


class BuildResult(object):

    def __init__(self):
        self.buildTime = None
        self.results = []
        self.success = False
        self.exception = None

    def setFailureResult(self,ex):
        self.exception = ex
        self.success = False

    def setSuccessResult(self,results):
        self.results = results
        self.success = True

class ScriptMetadata(object):
    def __init__(self):
        self.parameters = {}

    def add_script_parameter(self,p):
        self.parameters[p.name] = p

class ParameterType(object): pass
class NumberParameterType(ParameterType) : pass
class StringParameterType(ParameterType) : pass
class BooleanParameterType(ParameterType): pass


class InputParameter:

    def __init__(self):
        self.name = None
        self.shortDesc = None
        self.varType = None
        self.validValues = []
        self.defaultValue= None
        self.astNode = None

    @staticmethod
    def create(astNode,varname,varType, defaultValue,validValues =[],shortDesc = None):
        p = InputParameter()
        p.astNode = astNode
        p.defaultValue = defaultValue
        p.name = varname
        if shortDesc == None:
            p.shortDesc = varname
        else:
            p.shortDesc = shortDesc
        p.varType = varType
        p.validValues = validValues
        return p

    def setValue(self,newValue):
        #todo: check to make sure newValue can be cast correctly?
        if self.varType == NumberParameterType:
            self.astNode.n = newValue
        elif self.varType == StringParameterType:
            self.astNode.s = str(newValue)
        elif self.varType == BooleanParameterType:
            if ( newValue ):
                self.astNode.value.id = 'True'
            else:
                self.astNode.value.id = 'False'
        else:
            raise ValueError("Unknown Type of var: ", str(self.varType))

    def __str__(self):
        return "InputParmaeter: {name=%s, type=%s, defaultValue=%s" % ( self.name, str(self.varType), str(self.defaultValue) )

class BuildObjectCollector(object):
    """
    Allows a script to provide output objects
    """
    def __init__(self):
        self.outputObjects = []

    def build_object(self,shape):
        self.outputObjects.append(shape)

    def hasResults(self):
        return len(self.outputObjects) > 0

class ScriptExecutor(object):
    """
    executes a script in a given environment.
    """
    def __init__(self,environment,astTree):

        try:
            exec ( astTree ) in environment
        except Exception,ex:

            #an error here means there was a problem compiling the script
            #try to figure out what line the error was on
            traceback.print_exc()
            formatted_lines = traceback.format_exc().splitlines()
            lineText = ""
            for f in formatted_lines:
                if f.find(CQSCRIPT) > -1:
                    m = re.search("line\\s+(\\d+)",f,re.IGNORECASE )
                    if m and m.group(1):
                        lineText = m.group(1)
                    else:
                        lineText = 0

        sse = ScriptExecutionError()
        sse.line = int(lineText)
        sse.message = str(ex)
        raise sse

class ScriptExecutionError(Exception):
    """
        Represents a script syntax error.
        Useful for helping clients pinpoint issues with the script
        interactively
    """
    def __init__(self,line=None,message=None):
        if line is None:
            self.line = 0
        else:
            self.line = line

        if message is None:
            self.message = "Unknown Script Error"
        else:
            self.message = message

    def fullMessage(self):
        return self.__repr__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "ScriptError [Line %s]: %s" % ( self.line, self.message)

class EnvironmentBuilder(object):

    def __init__(self):
        self.env = {}

    def withRealBuiltins(self):
        return self.withBuiltins(__builtins__)

    def withBuiltins(self,dict):
        self.env['__builtins__'] = dict
        return self

    def addEntry(self,name, value):
        self.env[name] = value
        return self

    def build(self):
        return self.env

class VariableAssignmentChanger(ast.NodeTransformer):
    """

    """
    def __init__(self, overrides):
        self.overrides = overrides

    def modify_node(self, varname, node):
        if self.overrides.has_key(varname):
            new_value = self.overrides[varname]
            if type(node) == ast.Num:
                node.n = new_value
            elif type(node) == ast.Str:
                node.s = new_value
            else:
                raise ValueError("Unknown Assignment Type:" + str(type(node)))

    def visit_Assign(self, node):
        left_side = node.targets[0]
        if type(node.value) in [ast.Num, ast.Str]:
            self.modify_node(left_side.id, node.value)
        elif type(node.value) == ast.Tuple:
            # we have a multi-value assignment
            for n, v in zip(left_side.elts, node.value.elts):
                self.modify_node(n.id, v)
        return node

class ConstantAssignmentFinder(ast.NodeTransformer):
    """
    Visits a parse tree, and adds script parameters to the cqModel
    """

    def __init__(self,cqModel):
        self.cqModel = cqModel

    def handle_assignment(self,varname, valuenode):
        if type(valuenode) == ast.Num:
            self.cqModel.add_script_parameter(InputParameter.create(valuenode,varname,NumberParameterType,valuenode.n))
        elif type(valuenode) == ast.Str:
            self.cqModel.add_script_parameter(InputParameter.create(valuenode,varname,StringParameterType,valuenode.s))
        elif type(valuenode == ast.Name):
            if valuenode.value.Id == 'True':
                self.cqModel.add_script_parameter(InputParameter.create(valuenode,varname,BooleanParameterType,True))
            elif valuenode.value.Id == 'False':
                self.cqModel.add_script_parameter(InputParameter.create(valuenode,varname,BooleanParameterType,True))

    def visit_Assign(self, node):
        left_side = node.targets[0]
        if type(node.value) in [ast.Num, ast.Str, ast.Name]:
            self.handle_assignment(left_side.id,node.value)
        elif type(node.value) == ast.Tuple:
            # we have a multi-value assignment
            for n, v in zip(left_side.elts, node.value.elts):
                self.handle_assignment(n.id, v)
        return node