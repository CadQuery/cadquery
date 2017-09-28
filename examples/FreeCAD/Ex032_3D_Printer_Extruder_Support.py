# 3d printer for mounting hotend to X-carriage inspired by the P3steel Toolson
# edition - http://www.thingiverse.com/thing:1054909
import cadquery as cq


def move_to_center(cqObject, shape):
    '''
    Moves the origin of the current Workplane to the center of a given
    geometry object
    '''

    # transform to workplane local coordinates
    shape_center = shape.Center().sub(cqObject.plane.origin)

    # project onto plane using dot product
    x_offset = shape_center.dot(cqObject.plane.xDir)
    y_offset = shape_center.dot(cqObject.plane.yDir)

    return cqObject.center(x_offset, y_offset)

# Parameter definitions

main_plate_size_y = 67  # size of the main plate in y direction
main_plate_size_x = 50.  # size of the main plate in x direction
main_plate_thickness = 10.  # thickness of the main plate

wing_size_x = 10.  # size of the side wing supporting the bridge in x direction
wing_size_y = 10.  # size of the side wing supporting the bridge in y direction

bridge_depth = 35.  # depth of the bridge

support_depth = 18.  # depth of the bridge support

cutout_depth = 15.  # depth of the hotend cutout
cutout_rad = 8.     # radius of the cutout (cf groove mount sizes of E3D hotends)
cutout_offset = 2.  # delta radius of the second cutout (cf groove mount sizes of E3D hotends)

extruder_hole_spacing = 50.  # spacing of the extruder mounting holes (Wade's geared extruder)

m4_predrill = 3.7  # hole diameter for m4 tapping
m3_predrill = 2.5  # hole diameter for m3 tapping
m3_cbore = 5.      # counterbore size for m3 socket screw

mounting_hole_spacing = 28.  # spacing of the mounting holes for attaching to x-carriage

aux_hole_depth = 6.    # depth of the auxiliary holes at the sides of the object
aux_hole_spacing = 5.  # spacing of the auxiliary holes within a group
aux_hole_N = 2         # number of the auxiliary hole per group

# make the main plate
res = cq.Workplane('front').box(main_plate_size_x,
                                main_plate_size_y,
                                main_plate_thickness)


def add_wing(obj, sign=1):
    '''
    Adds a wing to the main plate, defined to keep the code DRY
    '''
    obj = obj.workplane()\
             .hLine(sign*wing_size_x)\
             .vLine(-wing_size_y)\
             .line(-sign*wing_size_x, -2*wing_size_y)\
             .close().extrude(main_plate_thickness)
    return obj

# add wings

# add right wing
res = res.faces('<Z').vertices('>XY')
res = add_wing(res)

# store sides of the plate for further reuse, their area is used later on to calculate "optimum" spacing of the aux hole groups
face_right = res.faces('>X[1]').val()
face_left = res.faces('>X[-2]').val()

# add left wing
res = res.faces('<Z').vertices('>Y').vertices('<X')
res = add_wing(res, -1)

# make the bridge for extruder mounting
wp = res.faces('>Z')  # select top face
e = wp.edges('>Y')    # select most extreme edge in Y direction

bridge_length = e.val().Length()  # the width of the bridge equals to the length of the selected edge

# draw the bridge x-section and extrude
res = e.vertices('<X'). \
        workplane(). \
        hLine(bridge_length). \
        vLine(-10). \
        hLine(-bridge_length). \
        close().extrude(bridge_depth)

faces = res.faces('>Z[1]')  # take all faces in Z direction and select the middle one; note the new selector syntax
edge = faces.edges('>Y')    # select the top edge of this face...
res = move_to_center(faces.workplane(), edge.val()).\
                     transformed(rotate=(0, 90, 0))  # ...and make a workplane that is centered in this edge and oriented along X direction

res = res.vLine(-support_depth).\
    line(-support_depth, support_depth).\
    close()  # draw a triangle

res = res.extrude(main_plate_size_x/2, both=True, clean=True)  # extrude the triangle, now the bridge has a nice support making it much more stiff

# Start cutting out a slot for hotend mounting
face = res.faces('>Y')  # select the most extreme face in Y direction, i.e. top ot the "bridge"
res = move_to_center(face.workplane(), face.edges('>Z').val())  # shift the workplane to the center of the most extreme edge of the bridge


def make_slot(obj, depth=None):
    '''
    Utility function that makes a slot for hotend mounting
    '''
    obj = obj.moveTo(cutout_rad, -cutout_depth).\
        threePointArc((0, -cutout_depth-cutout_rad),
                      (-cutout_rad, -cutout_depth)).\
        vLineTo(0).hLineTo(cutout_rad).close()

    if depth is None:
        obj = obj.cutThruAll()
    else:
        obj = obj.cutBlind(depth)

    return obj

res = make_slot(res, None)  # make the smaller slot

cutout_rad += cutout_offset  # increase the cutout radius...
res = make_slot(res.end().end(), -main_plate_thickness/2)  # ...and make a slightly larger slot

res = res.end().moveTo(0, 0) \
      .pushPoints([(-extruder_hole_spacing/2, -cutout_depth), (extruder_hole_spacing/2, -cutout_depth)]) \
      .hole(m4_predrill)  # add extruder mounting holes at the top of the bridge


# make additional slot in the bridge support which allows the hotend's radiator to fit
cutout_rad += 3*cutout_offset
res = make_slot(res.end().moveTo(0, 0).workplane(offset=-main_plate_thickness))

# add reinforcement holes
cutout_rad -= 2*cutout_offset
res = res.faces('>Z').workplane().\
          pushPoints([(-cutout_rad, -main_plate_thickness/4),
                      (cutout_rad, -main_plate_thickness/4)]).\
          hole(m3_predrill)

# add aux holes on the front face
res = res.moveTo(-main_plate_size_x/2., 0).workplane().rarray(aux_hole_spacing, 1, aux_hole_N, 1) \
                                                      .hole(m3_predrill, depth=aux_hole_depth)
res = res.moveTo(main_plate_size_x, 0).workplane().rarray(aux_hole_spacing, 1, aux_hole_N, 1) \
                                                  .hole(m3_predrill, depth=aux_hole_depth)

# make a hexagonal cutout
res = res.faces('>Z[1]')
res = res.workplane(offset=bridge_depth). \
      transformed(rotate=(0, 0, 90)). \
      polygon(6, 30).cutThruAll()

# make 4 mounting holes with cbores
res = res.end().moveTo(0, 0). \
      rect(mounting_hole_spacing,
           mounting_hole_spacing, forConstruction=True)

res = res.vertices(). \
          cboreHole(m3_predrill,
                    m3_cbore,
                    bridge_depth+m3_cbore/2)

# make cutout and holes for mounting of the fan
res = res.transformed(rotate=(0, 0, 45)). \
      rect(35, 35).cutBlind(-bridge_depth).end(). \
      rect(25, 25, forConstruction=True).vertices().hole(m3_predrill)


def make_aux_holes(workplane, holes_span, N_hole_groups=3):
    '''
    Utility function for creation of auxiliary mouting holes at the sides of the object
    '''
    res = workplane.moveTo(-holes_span/2).workplane().rarray(aux_hole_spacing, 1, aux_hole_N, 1) \
                                                     .hole(m3_predrill, depth=aux_hole_depth)
    for i in range(N_hole_groups-1):
        res = res.moveTo(holes_span/(N_hole_groups-1.)).workplane().rarray(aux_hole_spacing, 1, aux_hole_N, 1) \
                                                                     .hole(m3_predrill, depth=aux_hole_depth)

    return res

# make aux holes at the bottom
res = res.faces('<Y').workplane()
res = make_aux_holes(res, main_plate_size_x*2/3., 3)

# make aux holes at the side (@overhang)
res = res.faces('<X').workplane().transformed((90, 0, 0))
res = make_aux_holes(res, main_plate_size_x*2/3., 3)
res = res.faces('>X').workplane().transformed((90, 0, 0))
res = make_aux_holes(res, main_plate_size_x*2/3., 3)

# make aux holes at the side (@main plate)
res = res.faces('|X').edges('<Y').edges('>X')
res = res.workplane()
res = move_to_center(res, face_right)
res = res.transformed((90, 0, 0))
hole_sep = 0.5*face_right.Area()/main_plate_thickness
res = make_aux_holes(res, hole_sep, 2)

# make aux holes at the side (@main plate)
res = res.faces('|X').edges('<Y').edges('<X')
res = res.workplane()
res = move_to_center(res, face_left)
res = res.transformed((0, 180, 0))
hole_sep = 0.5*face_right.Area()/main_plate_thickness
res = make_aux_holes(res, hole_sep, 2)

# show the result
show_object(res)