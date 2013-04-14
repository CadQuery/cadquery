__author__ = 'dcowden'
"""
    Utilities exposed to users
"""
import math

# =================================================================================
# =================================================================================
# Spur-gear generation script
# (c) James Gregson, 2012
# Free for all use, including commercial, but do not redistribute.
# Use at your own risk.
#
# Notes:
#  - seems to work well for pressure angles up to about 30 degrees
# =================================================================================
# =================================================================================

# compute the root diameter of a gear with a given pressure-angle (pa)
# number of teeth (N), and pitch (P)
def gears_root_diameter( pa, N, P ):
    return (N-2.5)/P

# compute the base diameter of a gear with a given pressure-angle (pa)
# number of teeth (N), and pitch (P)
def gears_base_diameter( pa, N, P ):
    return gears_pitch_diameter( pa, N, P )*math.cos( pa*math.pi/180.0 )

# compute the outer diameter of a gear with a given pressure-angle (pa)
# number of teeth (N), and pitch (P)
def gears_outer_diameter( pa, N, P ):
    return gears_pitch_diameter( pa, N, P ) + 2.0*gears_addendum( pa, N, P )

# compute the outer diameter of a gear with a given pressure-angle (pa)
# number of teeth (N), and pitch (P)
def gears_pitch_diameter( pa, N, P ):
    return float(N)/float(P)

# compute the outer diameter of a gear with a given pressure-angle (pa)
# number of teeth (N) and pitch (P)
def gears_circular_pitch( pa, N, P ):
    return math.pi/float(P)

# compute the circular tooth thickness of a gear with a given
# pressure-angle (pa), number of teeth (N) and pitch (P)
def gears_circular_tooth_thickness( pa, N, P, backlash=0.05 ):
    return gears_circular_pitch( pa, N, P )/(2.0+backlash)

# compute the circular tooth angle of a gear with a given
# pressure-angle (pa), number of teeth (N) and pitch (P)
def gears_circular_tooth_angle( pa, N, P ):
    return gears_circular_tooth_thickness( pa, N, P )*2.0/gears_pitch_diameter( pa, N, P )

# compute the addendum height for a gear with a given
# pressure-angle (pa), number of teeth (N) and pitch (P)
def gears_addendum( pa, N, P ):
    return 1.0/float(P)

# compute the dedendum depth for a gear with a given
# pressur-angle (pa), number of teeth (N) and pitch (P)
def gears_dedendum( pa, N, P ):
    return 1.25/float(P)

# generates an involute curve from a circle of radius r up to theta_max radians
# with a specified number of steps
def gears_generate_involute( r, r_max, theta_max, steps=30 ):
    dtheta = theta_max / float(steps)
    x = []
    y = []
    theta = []
    rlast = r;
    for i in range( 0, steps+1 ):
        c = math.cos( i*dtheta )
        s = math.sin( i*dtheta )
        tx = r*( c + i*dtheta*s )
        ty = r*( s - i*dtheta*c )
        d = math.sqrt(tx*tx+ty*ty)
        if d > r_max:
            a = (r_max-rlast)/(d-rlast)
            tx = x[-1]*(1.0-a) + tx*a
            ty = y[-1]*(1.0-a) + ty*a
            ttheta = theta[-1]*(1.0-a) + math.atan2( ty, tx )*a
            x.append( tx )
            y.append( ty )
            theta.append( ttheta )
            break
        else:
            x.append( tx )
            y.append( ty )
            theta.append( math.atan2( ty, tx) )
    return x, y, theta

# returns the angle where an involute curve crosses a circle with a given radius
# or -1 on failure
def gears_locate_involute_cross_angle_for_radius( r, ix, iy, itheta ):
    for i in range( 0, len(ix)-1 ):
        r2 = ix[i+1]*ix[i+1] + iy[i+1]*iy[i+1]
        if r2 > r*r:
            r1 = math.sqrt( ix[i]*ix[i] + iy[i]*iy[i] )
            r2 = math.sqrt( r2 )
            a = (r-r1)/(r2-r1)
            return itheta[i]*(1.0-a) + itheta[i+1]*a
    return -1.0

# rotates the involute curve around the gear center in order to have the involute
# cross the x-axis at the pitch diameter
def gears_align_involute( Dp, ix, iy, itheta ):
    theta = -gears_locate_involute_cross_angle_for_radius( Dp/2.0, ix, iy, itheta )
    c = math.cos(theta)
    s = math.sin(theta)
    for i in range( 0, len(ix) ):
        tx = c*ix[i] - s*iy[i]
        ty = s*ix[i] + c*iy[i]
        ix[i] = tx
        iy[i] = ty
    return ix, iy

# reflects the input curve about the x-axis to generate the opposing face of
# a tooth
def gears_mirror_involute( ix, iy ):
    tx = []
    ty = []
    for i in range( 0, len(iy) ):
        tx.append( ix[len(iy)-1-i] )
        ty.append( -iy[len(iy)-1-i] )
    return tx, ty

# rotates the input curve by a given angle (in radians)
def gears_rotate( theta, ix, iy ):
    c = math.cos(theta)
    s = math.sin(theta)
    x = []
    y = []
    for i in range( 0, len(ix) ):
        tx = c*ix[i] - s*iy[i]
        ty = s*ix[i] + c*iy[i]
        x.append( tx )
        y.append( ty )
    return x, y

# translates the input curve by [dx, dy]
def gears_translate( dx, dy, ix, iy ):
    x = []
    y = []
    for i in range( 0, len(ix) ):
        x.append( ix[i]+dx )
        y.append( iy[i]+dy )
    return x, y

# generates a single tooth profile of a spur gear
def gears_make_tooth( pa, N, P ):
    ix, iy, itheta = gears_generate_involute( gears_base_diameter( pa, N, P )/2.0, gears_outer_diameter( pa, N, P )/2.0, math.pi/2.1 )
    ix.insert( 0, min( gears_base_diameter( pa, N, P )/2.0, gears_root_diameter( pa, N, P )/2.0 ) )
    iy.insert( 0, 0.0 )
    itheta.insert( 0, 0.0 )
    ix, iy = gears_align_involute( gears_pitch_diameter(pa, N, P), ix, iy, itheta )
    mx, my = gears_mirror_involute( ix, iy )
    mx, my = gears_rotate( gears_circular_tooth_angle( pa, N, P ), mx, my )
    ix.extend( mx )
    iy.extend( my )
    return ix, iy

# generates a spur gear with a given pressure angle (pa),
# number of teeth (N) and pitch (P)
def make_gear( pa, N, P ):
    tx, ty = gears_make_tooth( pa, N, P )
    x = []
    y = []
    for i in range( 0, N ):
        rx, ry = gears_rotate( float(i)*2.0*math.pi/float(N), tx, ty )
        x.extend( rx )
        y.extend( ry )
    x.append( x[0] )
    y.append( y[0] )
    return zip(x, y)