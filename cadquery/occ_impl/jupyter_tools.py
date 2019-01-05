from OCC.Display.WebGl.x3dom_renderer import X3DExporter
from OCC.gp import gp_Quaternion, gp_Vec
from uuid import uuid4
from math import tan
from xml.etree import ElementTree

from .geom import BoundBox

BOILERPLATE = \
'''
<link rel='stylesheet' type='text/css' href='http://www.x3dom.org/download/x3dom.css'></link>
<div style='height: {height}px; width: 100%;' width='100%' height='{height}px'>
    <x3d style='height: {height}px; width: 100%;' id='{id}' width='100%' height='{height}px'>
        <scene>
            <Viewpoint  position='{x},{y},{z}' centerOfRotation='{x0} {y0} {z0}' orientation='{rot}' fieldOfView='{fov}'></Viewpoint>
            {src}
        </scene>
    </x3d>
</div>
<script>
    if (document.getElementById('X3DOM_JS_MODULE') == null){{
        var scr  = document.createElement('script');
        head = document.head || document.getElementsByTagName('head')[0];
        scr.src = 'http://www.x3dom.org/download/x3dom.js';
        scr.async = false;
        scr.id = 'X3DOM_JS_MODULE';
        scr.onload = function () {{
           x3dom.reload();
        }}
        head.insertBefore(scr, head.lastChild);
    }}
    else if (typeof x3dom != 'undefined') {{ //call reload only if x3dom already loaded
        x3dom.reload();
    }}

    //document.getElementById('{id}').runtime.fitAll()
</script>
'''

#https://stackoverflow.com/questions/950087/how-do-i-include-a-javascript-file-in-another-javascript-file
#better if else

ROT = (0.77,0.3,0.55,1.28)
ROT = (0.,0,0,1.)
FOV = 0.2

def add_x3d_boilerplate(src, height=400, center=(0,0,0), d=(0,0,15), fov=FOV, rot='{} {} {} {} '.format(*ROT)):

    return BOILERPLATE.format(src=src,
                              id=uuid4(),
                              height=height,
                              x=d[0],
                              y=d[1],
                              z=d[2],
                              x0=center[0],
                              y0=center[1],
                              z0=center[2],
                              fov=fov,
                              rot=rot)

def x3d_display(shape,
                vertex_shader=None,
                fragment_shader=None,
                export_edges=True,
                color=(1,1,0),
                specular_color=(1,1,1),
                shininess=0.4,
                transparency=0.4,
                line_color=(0,0,0),
                line_width=2.,
                mesh_quality=.3):

        # Export to XML <Scene> tag
        exporter = X3DExporter(shape,
                               vertex_shader,
                               fragment_shader,
                               export_edges,
                               color,
                               specular_color,
                               shininess,
                               transparency,
                               line_color,
                               line_width,
                               mesh_quality)

        exporter.compute()
        x3d_str = exporter.to_x3dfile_string(shape_id=0)
        xml_et = ElementTree.fromstring(x3d_str)
        scene_tag = xml_et.find('./Scene')

        # Viewport Parameters
        bb = BoundBox._fromTopoDS(shape)
        d = max(bb.xlen,bb.ylen,bb.zlen)
        c = bb.center

        vec = gp_Vec(0,0,d/1.5/tan(FOV/2))
        quat = gp_Quaternion(*ROT)
        vec = quat*(vec) + c.wrapped

        # return boilerplate + Scene
        return add_x3d_boilerplate(ElementTree.tostring(scene_tag).decode('utf-8'),
                                   d=(vec.X(),vec.Y(),vec.Z()),
                                   center=(c.x,c.y,c.z))
