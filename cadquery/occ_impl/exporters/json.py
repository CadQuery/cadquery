"""
    Objects that represent
    three.js JSON object notation
    https://github.com/mrdoob/three.js/wiki/JSON-Model-format-3.0
"""

JSON_TEMPLATE = """\
{
    "metadata" :
    {
        "formatVersion" : 3,
        "generatedBy"   : "ParametricParts",
        "vertices"      : %(nVertices)d,
        "faces"         : %(nFaces)d,
        "normals"       : 0,
        "colors"        : 0,
        "uvs"           : 0,
        "materials"     : 1,
        "morphTargets"  : 0
    },

    "scale" : 1.0,

    "materials": [    {
    "DbgColor" : 15658734,
    "DbgIndex" : 0,
    "DbgName" : "Material",
    "colorAmbient" : [0.0, 0.0, 0.0],
    "colorDiffuse" : [0.6400000190734865, 0.10179081114814892, 0.126246120426746],
    "colorSpecular" : [0.5, 0.5, 0.5],
    "shading" : "Lambert",
    "specularCoef" : 50,
    "transparency" : 1.0,
    "vertexColors" : false
    }],

    "vertices": %(vertices)s,

    "morphTargets": [],

    "normals": [],

    "colors": [],

    "uvs": [[]],

    "faces": %(faces)s
}
"""


class JsonMesh(object):
    def __init__(self):

        self.vertices = []
        self.faces = []
        self.nVertices = 0
        self.nFaces = 0

    def addVertex(self, x, y, z):
        self.nVertices += 1
        self.vertices.extend([x, y, z])

    # add triangle composed of the three provided vertex indices
    def addTriangleFace(self, i, j, k):
        # first position means justa simple triangle
        self.nFaces += 1
        self.faces.extend([0, int(i), int(j), int(k)])

    """
        Get a json model from this model.
        For now we'll forget about colors, vertex normals, and all that stuff
    """

    def toJson(self):
        return JSON_TEMPLATE % {
            "vertices": str(self.vertices),
            "faces": str(self.faces),
            "nVertices": self.nVertices,
            "nFaces": self.nFaces,
        }
