from OCC.Display.WebGl.x3dom_renderer import X3DExporter
from uuid import uuid1

N_HEADER_LINES = 10
BOILERPLATE = \
'''
<link rel='stylesheet' type='text/css' href='http://www.x3dom.org/download/x3dom.css'></link>
<div style='height: {height}px; width: 100%;' width='100%' height='{height}px'>
    <x3d style='height: {height}px; width: 100%;' id='{id}' width='100%' height='{height}px'>
        <scene>
            <Viewpoint  position='0,0,0' orientation='0.77 0.32 0.55 1.28' fieldOfView='0.2'></Viewpoint>
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
        head.insertBefore(scr, head.lastChild);
    }}
    x3dom.reload();
    document.getElementById('{id}').runtime.fitAll()
</script>
'''

def add_x3d_boilerplate(src, height=400):

    return BOILERPLATE.format(src=src, id=uuid1(), height=height)

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
        x3d_str = exporter.to_x3dfile_string()
        x3d_str = '\n'.join(x3d_str.splitlines()[N_HEADER_LINES:])
        
        return add_x3d_boilerplate(x3d_str)