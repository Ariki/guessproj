#!python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function

__author__ = 'Alexei Ardyakov'
__version__ = '0.05'
__license__ = 'MIT'

import codecs
import os
import re
import sys
from functools import partial
from pyproj import Proj, transform
from scipy.optimize import leastsq

# osgeo package is optional (used for WKT output and projstring normalization)
try:
    from osgeo import osr
except:
    osr = False

# Python version compatibility
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str


def to_str(s, encoding='utf-8'):
    """Converts raw bytes or Unicode string to str type
    (which is Unicode string in Python 3 and raw bytes in Python 2)
    """
    if s is None:
        return None
    if isinstance(s, str):
        return s
    if PY3 and isinstance(s, bytes):
        return s.decode(encoding)
    if not PY3 and isinstance(s, unicode):
        return s.encode(encoding)
    raise ValueError('Cannot convert {0} to str'.format(s))


def to_unicode(s, encoding='utf-8'):
    """Converts raw bytes or Unicode string to Unicode"""
    if s is None:
        return None
    # For Python 3, unicode is defined above as an alias for str
    if isinstance(s, unicode):
        return s
    if isinstance(s, bytes):
        return s.decode(encoding)
    raise ValueError('Cannot convert {0} to Unicode'.format(s))


def refine_projstring(projstring):
    """Refines projstring using osgeo package"""
    if osr:
        srs = osr.SpatialReference()
        srs.ImportFromProj4(to_str(projstring))
        return srs.ExportToProj4()
    return projstring


def target_func_template(points, src_proj, tgt_template, params):
    """Target function template (the real target function is a result
    of partial application of the template with first 3 arguments known)
    """
    tgt_proj = tgt_template.format(*params)
    p1 = Proj(to_str(src_proj))
    p2 = Proj(to_str(tgt_proj))
    result = []
    for pt in points:
        if len(pt[0]) == 2:
            tpt = transform(p1, p2, pt[0][0], pt[0][1])
        elif len(pt[0]) == 3:
            tpt = transform(p1, p2, pt[0][0], pt[0][1], pt[0][2])
        else:
            raise ValueError('Two or three coordinates expected')
        result.append(pt[1][0] - tpt[0])
        result.append(pt[1][1] - tpt[1])
        if len(pt[0]) == 3 and len(pt[1]) == 3:
            result.append(pt[0][2] - tpt[2])
    return result
    

def find_residuals(src_proj, tgt_proj, points):
    """Transforms the points and calculates the residuals"""
    p1 = Proj(to_str(src_proj))
    p2 = Proj(to_str(tgt_proj))
    residuals = []
    for pt in points:
        if len(pt[0]) == 2:
            tpt = transform(p1, p2, pt[0][0], pt[0][1])
        elif len(pt[0]) == 3:
            tpt = transform(p1, p2, pt[0][0], pt[0][1], pt[0][2])
        else:
            raise ValueError('Two or three coordinates expected')
        pt_residuals = [pt[1][i] - tpt[i] for i in range(len(pt[1]))]
        residuals.append(pt_residuals)
    return residuals
    

def find_params(src_proj, tgt_known, tgt_unknown, points):
    """Finds unknown params of target projection
    using least squares method
    """
    # Sorting params (some of them can have dot separated index)
    param_list = []
    for param_dict, is_known in ((tgt_known, True), (tgt_unknown, False)):
        for k in param_dict.keys():
            if '.' in k:
                k1, k2 = k.split('.')
                k2 = int(k2)
            else:
                k1, k2 = k, 0
            param_list.append((k1, k2, param_dict[k], is_known))
    param_list.sort()
    # Constructing target projection template
    start_values, var_names = [], []
    tgt_template = ''
    var_index = 0
    for p in param_list:
        if p[1] == 0:
            tgt_template += ' +{0}'.format(p[0])
        else:
            tgt_template += ','
        if p[3]: # Known value
            if p[2] is not None:
                if p[1] == 0:
                    tgt_template += '={0}'.format(p[2])
                else:
                    tgt_template += '{0}'.format(p[2])
        else: # Unknown value
            start_values.append(p[2])
            if p[1] == 0:
                var_names.append(p[0])
                tgt_template += '='
            else:
                var_names.append('{0}.{1}'.format(p[0], p[1]))
            tgt_template += '{' + str(var_index) + '}'
            var_index += 1
    tgt_template = tgt_template.strip()
    # If all parameters are known, calculate the residuals
    if not tgt_unknown:
        return (
            refine_projstring(tgt_template),
            {},
            find_residuals(src_proj, tgt_template, points)
            )
    # Creating target function
    tgt_func = partial(target_func_template,
                       points, src_proj, tgt_template)
    # Solving the problem
    x, cov_x, infodict, mesg, ier = leastsq(
        tgt_func, start_values, ftol=1e-12, full_output=True)
    # Formatting outputs
    if ier not in (1, 2, 3, 4):
        return None, None, None
    result_projstring = refine_projstring(tgt_template.format(*x))
    result_dict = dict(zip(var_names, x))
    fvec = infodict['fvec']
    residuals = []
    i = 0
    for pt in points:
        if len(pt[0]) == 3 and len(pt[1]) == 3:
            residuals.append(tuple(fvec[i:i + 3]))
            i += 3
        else:
            residuals.append(tuple(fvec[i:i + 2]))
            i += 2
    return result_projstring, result_dict, residuals


def parse_arguments(argv):
    """Parses command line arguments of the program"""
    src_params = []
    known, unknown, options = {}, {}, {}
    filename = None
    parsing_target = False
    for arg in argv[1:]:
        arg = to_unicode(arg, sys.getfilesystemencoding())
        if arg.startswith('-'):
            splitarg = arg.split('=', 1)
            if len(splitarg) == 2:
                options[splitarg[0]] = splitarg[1]
            else:
                options[arg] = True
        elif parsing_target:
            if arg.startswith('+'):
                param_re = re.compile(r'^\+([0-9a-zA-Z_]+)([=~].*)?$')
                m = param_re.match(arg)
                if not m:
                    raise ValueError('Invalid parameter: {0}'.format(arg))
                pname, pvalue = m.groups()
                if not pvalue:
                    known[pname] = None
                else:
                    subvalues = pvalue.split(',')
                    for i, sv in enumerate(subvalues):
                        extpname = pname + ('.' + str(i) if i else '')
                        if sv.startswith('~'):
                            unknown[extpname] = float(sv[1:])
                        elif sv.startswith('=~'):
                            unknown[extpname] = float(sv[2:])
                        elif sv.startswith('='):
                            known[extpname] = sv[1:]
                        else:
                            known[extpname] = sv
            else:
                if filename:
                    raise ValueError('Multiple input files are not supported')
                filename = arg
        else:
            if arg == '+to':
                parsing_target = True
            elif arg.startswith('+'):
                src_params.append(arg)
            else:
                raise ValueError('Unexpected token: {0}'.format(arg))
    if src_params:
        src_proj = ' '.join(src_params)
    else:
        src_proj = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
    return (src_proj, known, unknown, options, filename)


def parse_coord(s):
    """Parses a value of coordinate in decimal or DMS format"""
    if s is None:
        raise TypeError('Coordinate value is None')
    ss = to_str(s).replace(',', '.')
    try:
        f = float(ss)
    except:
        dms_re = re.compile(r'^([+-])?'
                            r'(?:(\d{0,3}(?:\.\d*)?)?d)?'
                            r"(?:(\d{0,2}(?:\.\d*)?)?')?"
                            r'(?:(\d{0,2}(?:\.\d*)?)?")?$')
        m = dms_re.match(ss)
        if not m:
            raise ValueError('`{0}` is not a valid coordinate value'.format(s))
        g = m.groups()
        if g[1] in ('', None) and g[2] in ('', None) and g[3] in ('', None):
            raise ValueError('`{0}` is not a valid coordinate value'.format(s))
        f = 0
        if g[1]:
            f += float(g[1])
        if g[2]:
            mf = float(g[2])
            if mf >= 60:
                raise ValueError('Invalid value for minutes: {0}'.format(mf))
            f += mf / 60.0
        if g[3]:
            sf = float(g[3])
            if sf >= 60:
                raise ValueError('Invalid value for minutes: {0}'.format(mf))
            f += sf / 3600.0
        if g[0] == '-':
            f = -f
    return f


def read_points(filename, encoding='utf-8'):
    """Reads points from a file"""
    points = []
    with codecs.open(filename, 'r', encoding) as fp:
        for line in fp:
            tokens = line.strip().split()
            if not tokens or not tokens[0] or tokens[0].startswith('#'):
                continue
            number_count = len(tokens)
            for i, t in enumerate(tokens):
                try:
                    d = parse_coord(t)
                except:
                    number_count = i
                    break
            number_count = min((number_count, 6))
            if number_count == 5:
                number_count = 4
            if number_count < 4:
                raise ValueError('')
            tokens = line.strip().split(None, number_count)
            if number_count == 4:
                points.append((
                    tuple(map(parse_coord, tokens[0:2])),
                    tuple(map(parse_coord, tokens[2:4])),
                    tokens[4] if len(tokens) > 4 else '',
                    ))
            elif number_count == 6:
                points.append((
                    tuple(map(parse_coord, tokens[0:3])),
                    tuple(map(parse_coord, tokens[3:6])),
                    tokens[6] if len(tokens) > 6 else '',
                    ))
    return points


def usage_help(program_name):
    """Returns usage help string"""
    return ('Usage: {0} [--opts] +src_opts[=arg,] '
            '+to +tgt_opts[=[~]arg,] filename'.format(program_name))


def format_residuals(points, residuals):
    """Returns the residuals as a text string"""
    s = 'Residuals:\n'
    for i, pt in enumerate(points):
        r = residuals[i]
        if len(r) == 2:
            s += '{0}\t{1}\t\t{2}\n'.format(r[0], r[1], pt[2])
        else:
            s += '{0}\t{1}\t{2}\t{3}\n'.format(r[0], r[1], r[2], pt[2])
    return s


def to_wkt(projstring, esri=False, pretty=False):
    """Returns projection parameters as well-known text"""
    if not osr:
        raise ImportError('Package osgeo not found')
    srs = osr.SpatialReference()
    srs.ImportFromProj4(to_str(projstring))
    if esri:
        srs.MorphToESRI()
    return srs.ExportToPrettyWkt() if pretty else srs.ExportToWkt()


def to_mapinfo(projstring):
    """Returns projection parameters as MapInfo CoordSys definition"""
    if not osr:
        raise ImportError('Package osgeo not found')
    srs = osr.SpatialReference()
    srs.ImportFromProj4(to_str(projstring))
    return srs.ExportToMICoordSys()


def generate_output(outfile, result_projstring, options, points, residuals):
    """Outputs results in specified format"""
    if '--proj' in options or '--proj4' in options:
        outfile.write(result_projstring)
    elif '--wkt' in options:
        outfile.write(to_wkt(result_projstring, pretty='--pretty' in options))
    elif '--esri' in options:
        outfile.write(
            to_wkt(result_projstring, esri=True, pretty='--pretty' in options))
    elif '--mapinfo' in options:
        outfile.write(to_mapinfo(result_projstring))
    else:
        outfile.write(result_projstring)
        outfile.write('\n')
        outfile.write(format_residuals(points, residuals))
    outfile.write('\n')


def arg_main(argv, outfile):
    """The variant of main() that expects sys.argv and sys.stdout
    as function arguments (for use in tests or wrapper scripts)
    """
    src_proj, known, unknown, options, filename = parse_arguments(argv)
    if '-h' in options or '--help' in options:
        outfile.write(usage_help(argv[0]))
        outfile.write('\n')
        return 0
    encoding = options.get('--encoding', 'utf-8')
    points = read_points(filename, encoding)
    result_projstring, result_dict, residuals = find_params(
        src_proj, known, unknown, points)
    if result_projstring:
        generate_output(outfile, result_projstring, options, points, residuals)
        return 0
    else:
        if not(set(options.keys()) &
               set(['--proj', '--proj4', '--wkt', '--esri',])):
            outfile.write('Solution not found\n')
        return 1


def main():
    """The script entry point used in setup.py"""
    try:
        return arg_main(sys.argv, sys.stdout)
    except Exception as ex:
        sys.stderr.write(str(ex))
        sys.stderr.write('\n')
        return 1


if __name__ == '__main__':
    sys.exit(main())
