    #Copyright 2009-2016 Seyed Hessam Moosavi Mehr, Juergen Probst
    #This program is free software; you can redistribute it and/or modify
    #it under the terms of the GNU General Public License as published by
    #the Free Software Foundation; either version 3 of the License, or
    #(at your option) any later version.

    #This program is distributed in the hope that it will be useful,
    #but WITHOUT ANY WARRANTY; without even the implied warranty of
    #MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #GNU General Public License for more details.

    #You should have received a copy of the GNU General Public License
    #along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, print_function
from subprocess import check_output
import re
import numpy as np


meep_call = 'mpirun -np %(num_procs)s meep-mpi'

mpbdata_call = ('mpb-data '
                '-x%(tiles_x)s '
                '-y%(tiles_y)s '
                '-o%(output_file)s '
                '%(h5_file)s:%(dataset)s')
epsh5topng_call_2D = 'h5topng -S3 -Zrcbluered -oepsilon.png %(h5_file)s'
epsh5topng_call_3D = 'h5topng -0z0 -S3 -Zrcbluered -oepsilon.png %(h5_file)s'
epsh5topng_call_3D_cross_sect = ('h5topng -0x0 -S3 -Zrcbluered '
                              '-oepsilonslab.png %(h5_file)s')


fieldh5topng_call = ('h5topng %(sliceparam)s -RZcdkbluered -C%(eps_file)s %(h5_file)s')
pwrh5topng_call = ('h5topng %(sliceparam)s -chot -C%(eps_file)s '
                        '-o%(output_file)s %(h5_file)s')
display_png_call = 'display  %(files)s'

# get mpb version:
meepversion = 'n/a'
for meep in ['meep-mpi', 'meep']:
    try:
        meepversionline = check_output(
            [meep, '--version'], universal_newlines=True)
        # MPB made it hard to check the version. The line even changed
        # in version 1.5. Look for first non-alpha part, this might be
        # what we are looking for:
        try:
            meepversion = re.search(
                '\s([0-9.]*)[,\s]',
                meepversionline).groups()[0]
        except AttributeError:
            # did not find anything:
            meepversion = 'n/a'
        break
    except OSError:
        pass


# The source band width used in the simulations of single modes,
# in which the mode patterns are generated:
mode_pattern_sim_df = 0.01



default_resolution = 32

def default_band_func(poi, outputfunc):
    """Return a string which will be supplied to (run %s) as a bandfunction.

    poi: k-points of interest, list of 3-tuples.
    outputfunc: mpb outputfunction, e.g. 'output-efield-z'

    """
    return (
        '\n    display-group-velocities'
        '\n    display-zparities display-yparities' +
        ''.join(
            [
                '\n    (output-at-kpoint (vector3 {0}) {1})'.format(
                    ' '.join(str(c) for c in vec),
                    outputfunc
                )
                for vec in poi
            ]
        )
    )

output_funcs_te = ['fix-hfield-phase', 'output-hfield-z']
output_funcs_tm = ['fix-efield-phase', 'output-efield-z']
# these are used for (run) function without specific modes:
output_funcs_other = output_funcs_te + output_funcs_tm

temporary_epsh5 = './temporary_eps.h5'
temporary_h5 = './temporary.h5'
temporary_h5_folder = './patterns~/'

isQuiet = False

log_format = "%(asctime)s %(levelname)s: %(message)s"
log_datefmt = "%d.%m.%Y %H:%M:%S"

template = '''%(initcode)s

(set! geometry-lattice %(lattice)s)

(set! resolution %(resolution)s)

(set! mesh-size %(meshsize)s)

(set! num-bands %(numbands)s)

(set! k-points %(kspace)s)

(set! geometry (list %(geometry)s))

%(runcode)s

%(postcode)s

(display-eigensolver-stats)'''



#####################################################
###          bandplotter defaults                 ###
#####################################################

fig_size = (12, 9)

draw_bands_formatstr = 'o-'
# keyword arguments for band diagram (matplotlib.lines.Line2D properties,
# see :class:`~matplotlib.lines.Line2D` for details.):
draw_bands_kwargs = {'linewidth' : 2}
hide_band_gap = False;

# default kwargs for the tick labels for the k-vec-axis of band diagrams:
# (will be forwarded to underlying matplotlib.text.Text objects)
xticklabels_kwargs={'rotation':0, 'horizontalalignment':'center'}
# xticklabels_kwargs used when one of the labels strings is longer than
# long_xticklabels_when_longer_than:
long_xticklabels_kwargs={'rotation':45, 'horizontalalignment':'right'}
long_xticklabels_when_longer_than = 12

# Text added to gaps drawn in the band diagrams,
# formatted with default_gaptext.format(gapsize_in_percent):
default_gaptext='gap size: {0:.2f}%'
# for locale-aware formatting e.g.:
#default_gaptext='gap size: {0:.4n}%'

# Minimum gap size (normalized, i.e. \Delta\omega/\omega_{center});
# gaps smaller than this will not be drawn in the band diagram:
min_gapsize = 0.0

default_x_axis_hint = 5 # 5 equally spaced ticks, labeled with k-vector
default_y_axis_label = r'frequency $\omega a/2\pi c$'
default_x_axis_label = 'wave vector {0}'
# the x_axis_label used when showing high symmetry point labels on the k
# axis: Note: I am not entirely satisfied with this title. How do you
# really call it? 'Brilluoin zone symmetry points'? 'Wave vector
# direction'? (this last one is good, but we also see the magnitude,
# when e.g. going from Gamma to M etc.) 'Wave vector point in brilluoin
# zone'? (too long)
default_kspace_axis_label = 'wave vector'

default_kvecformatter_format_str = '({0:.2f}  {1:.2f}  {2:.2f})'
# make it locale-aware:
#default_kvecformatter_format_str = '({0:.2n}  {1:.2n}  {2:.2n})'
# other possibilities:
#default_kvecformatter_format_str = r'$\binom{{ {0} }}{{ {1} }}$'
# unfortunately, \stackrel[3]{}{}{} does not work, so it looks bad:
#default_kvecformatter_format_str = \
#    r'$\left(\stackrel{{ {0} }}{{ \stackrel{{ {1} }}{{ {2} }} }}\right)$'
#default_kvecformatter_format_str ='{0}\n{1}\n{2}'

# Show fractions in tick labels of k-axis instead of floating point values:
ticks_fractions = True
# Always show a floating point value if the resulting fraction's denominator
# is greater than:
tick_max_denominator = 1000

# If correct_x_axis is set to True, the bands are plotted versus
# x-values which are equidistant according to the Euclidean distance
# between the k-vectors. That way distortions are avoided which occur
# when plotting versus the k-index.
correct_x_axis = True

color_by_parity_marker_size = 60

add_epsilon_as_inset = False
# The valid location codes are:
#     'upper right'  : 1,
#     'upper left'   : 2,
#     'lower left'   : 3,
#     'lower right'  : 4,
#     'right'        : 5,
#     'center left'  : 6,
#     'center right' : 7,
#     'lower center' : 8,
#     'upper center' : 9,
#     'center'       : 10,
epsilon_inset_location = 4
epsilon_inset_zoom = 0.5
epsilon_inset_transpose = False




# In the field pattern distribution plot, should the real and imaginary
# parts be on top of each other? Otherwise, they go next to each other:
field_dist_vertical_cmplx_comps=True
field_dist_filetype = 'pdf'


contour_lines = {'colors':'k',
                 'linestyles':['dashed','solid'],
                 'linewidths':1.0}
contour_plain = {'linewidths':1.0}
contour_filled = {}
colorbar_style = {'extend':'both','shrink':0.8}



# uncomment to use locale-aware formatting on the numbers along the y-axis:
#import matplotlib.pyplot as plt
#plt.rcParams['axes.formatter.use_locale'] = True

