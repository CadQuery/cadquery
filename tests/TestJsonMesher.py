import unittest
from JsonUtils import JsonMesh
import FreeCAD
from FreeCAD import Part
from FreeCAD import Vector

"""
    WARNING: set FREECAD_HOME for these tests to work!
"""
class TestJSonModel(unittest.TestCase):
    
    def setUp(self):
        self.mesh = JsonMesh();
        
    def testOneFace(self):
        mesh = self.mesh;
        mesh.addVertex(0.0,0.0,0.0);
        mesh.addVertex(1.0,1.0,0.0);
        mesh.addVertex(-1.0,1.0,0);
        mesh.addTriangleFace(0, 1, 2);
        self.assertEqual(3*3,len(mesh.vertices));
        self.assertEqual(1+3,len(mesh.faces));    
                
    def testSphere(self):
   
       #make a sphere
       p = Part.makeSphere(2.0);
       t = p.tessellate(0.01); #a pretty fine mesh
        
       #add vertices
       for vec in t[0]:
           self.mesh.addVertex(vec.x, vec.y, vec.z);

       #add faces
       for f in t[1]:
           self.mesh.addTriangleFace(f[0],f[1], f[2]);
           
       #make resulting json
       self.mesh.buildTime = 0.1;
       js = self.mesh.toJson();
       
       #make sure the mesh has like >1000 vertices
       self.assertTrue(self.mesh.nVertices > 1000);
       self.assertTrue(self.mesh.nFaces > 1000);
