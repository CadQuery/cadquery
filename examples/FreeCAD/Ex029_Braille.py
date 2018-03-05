# -*- coding: utf-8 -*-

from __future__ import division

from collections import namedtuple

import cadquery as cq

# text_lines is a list of text lines.
# "CadQuery" in braille (converted with braille-converter:
# https://github.com/jpaugh/braille-converter.git).
text_lines = [u'⠠ ⠉ ⠁ ⠙ ⠠ ⠟ ⠥ ⠻ ⠽']
# See http://www.tiresias.org/research/reports/braille_cell.htm for examples
# of braille cell geometry.
horizontal_interdot = 2.5
vertical_interdot = 2.5
horizontal_intercell = 6
vertical_interline = 10
dot_height = 0.5
dot_diameter = 1.3

base_thickness = 1.5

# End of configuration.
BrailleCellGeometry = namedtuple('BrailleCellGeometry',
                                 ('horizontal_interdot',
                                  'vertical_interdot',
                                  'intercell',
                                  'interline',
                                  'dot_height',
                                  'dot_diameter'))


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __len__(self):
        """Necessary to have it accepted as input to CadQuery"""
        return 2

    def __getitem__(self, index):
        """Necessary to have it accepted as input to CadQuery"""
        return (self.x, self.y)[index]

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)


def braille_to_points(text, cell_geometry):
    # Unicode bit pattern (cf. https://en.wikipedia.org/wiki/Braille_Patterns).
    mask1 = 0b00000001
    mask2 = 0b00000010
    mask3 = 0b00000100
    mask4 = 0b00001000
    mask5 = 0b00010000
    mask6 = 0b00100000
    mask7 = 0b01000000
    mask8 = 0b10000000
    masks = (mask1, mask2, mask3, mask4, mask5, mask6, mask7, mask8)

    # Corresponding dot position
    w = cell_geometry.horizontal_interdot
    h = cell_geometry.vertical_interdot
    pos1 = Point(0, 2 * h)
    pos2 = Point(0, h)
    pos3 = Point(0, 0)
    pos4 = Point(w, 2 * h)
    pos5 = Point(w, h)
    pos6 = Point(w, 0)
    pos7 = Point(0, -h)
    pos8 = Point(w, -h)
    pos = (pos1, pos2, pos3, pos4, pos5, pos6, pos7, pos8)

    # Braille blank pattern (u'\u2800').
    blank = u'⠀'
    points = []
    # Position of dot1 along the x-axis (horizontal).
    character_origin = 0
    for c in text:
        for m, p in zip(masks, pos):
            delta_to_blank = ord(c) - ord(blank)
            if (m & delta_to_blank):
                points.append(p + Point(character_origin, 0))
        character_origin += cell_geometry.intercell
    return points


def get_plate_height(text_lines, cell_geometry):
    # cell_geometry.vertical_interdot is also used as space between base
    # borders and characters.
    return (2 * cell_geometry.vertical_interdot +
            2 * cell_geometry.vertical_interdot +
            (len(text_lines) - 1) * cell_geometry.interline)


def get_plate_width(text_lines, cell_geometry):
    # cell_geometry.horizontal_interdot is also used as space between base
    # borders and characters.
    max_len = max([len(t) for t in text_lines])
    return (2 * cell_geometry.horizontal_interdot +
            cell_geometry.horizontal_interdot +
            (max_len - 1) * cell_geometry.intercell)


def get_cylinder_radius(cell_geometry):
    """Return the radius the cylinder should have

    The cylinder have the same radius as the half-sphere that make the dots
    (the hidden and the shown part of the dots).
    The radius is such that the spherical cap with diameter
    cell_geometry.dot_diameter has a height of cell_geometry.dot_height.
    """
    h = cell_geometry.dot_height
    r = cell_geometry.dot_diameter / 2
    return (r ** 2 + h ** 2) / 2 / h


def get_base_plate_thickness(plate_thickness, cell_geometry):
    """Return the height on which the half spheres will sit"""
    return (plate_thickness +
            get_cylinder_radius(cell_geometry) -
            cell_geometry.dot_height)


def make_base(text_lines, cell_geometry, plate_thickness):
    base_width = get_plate_width(text_lines, cell_geometry)
    base_height = get_plate_height(text_lines, cell_geometry)
    base_thickness = get_base_plate_thickness(plate_thickness, cell_geometry)
    base = cq.Workplane('XY').box(base_width, base_height, base_thickness,
                                  centered=(False, False, False))
    return base


def make_embossed_plate(text_lines, cell_geometry):
    """Make an embossed plate with dots as spherical caps

    Method:
        - make a thin plate, called base, on which sit cylinders
        - fillet the upper edge of the cylinders so to get pseudo half-spheres
        - make the union with a thicker plate so that only the sphere caps stay
          "visible".
    """
    base = make_base(text_lines, cell_geometry, base_thickness)

    dot_pos = []
    base_width = get_plate_width(text_lines, cell_geometry)
    base_height = get_plate_height(text_lines, cell_geometry)
    y = base_height - 3 * cell_geometry.vertical_interdot
    line_start_pos = Point(cell_geometry.horizontal_interdot, y)
    for text in text_lines:
        dots = braille_to_points(text, cell_geometry)
        dots = [p + line_start_pos for p in dots]
        dot_pos += dots
        line_start_pos += Point(0, -cell_geometry.interline)

    r = get_cylinder_radius(cell_geometry)
    base = base.faces('>Z').vertices('<XY').workplane() \
        .pushPoints(dot_pos).circle(r) \
        .extrude(r)
    # Make a fillet almost the same radius to get a pseudo spherical cap.
    base = base.faces('>Z').edges() \
        .fillet(r - 0.001)
    hidding_box = cq.Workplane('XY').box(
        base_width, base_height, base_thickness, centered=(False, False, False))
    result = hidding_box.union(base)
    return result

_cell_geometry = BrailleCellGeometry(
    horizontal_interdot,
    vertical_interdot,
    horizontal_intercell,
    vertical_interline,
    dot_height,
    dot_diameter)

if base_thickness < get_cylinder_radius(_cell_geometry):
    raise ValueError('Base thickness should be at least {}'.format(dot_height))

show_object(make_embossed_plate(text_lines, _cell_geometry))
