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
from osgeo import osr
from scipy.optimize import leastsq

# Python version compatibility
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int
    
# Enable exceptions in osgeo.osr
osr.UseExceptions()


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
    """Reformats the projstring in standardized way"""
    srs = osr.SpatialReference()
    srs.ImportFromProj4(to_str(projstring))
    return srs.ExportToProj4()
    

def calc_residuals(src_srs, tgt_srs, modifiers, points):
    """Transforms the points and calculates the residuals"""
    transform = osr.CoordinateTransformation(src_srs, tgt_srs)
    r = []
    for pt in points:
        tpt = transform.TransformPoint(*pt[0])
        r.append(pt[1][0] - (tpt[0] * modifiers['--k_0'] + modifiers['--x_0']))
        r.append(pt[1][1] - (tpt[1] * modifiers['--k_0'] + modifiers['--y_0']))
        if len(pt[0]) == 3 and len(pt[1]) == 3:
            r.append(pt[0][2] - (tpt[2] + modifiers['--z_0']))
    return r


def group_residuals(values, points):
    """Groups residuals basing on points list and returns a list of tuples"""
    result = []
    i = 0
    for pt in points:
        if len(pt[0]) == 3 and len(pt[1]) == 3:
            result.append(tuple(values[i:i + 3]))
            i += 3
        else:
            result.append(tuple(values[i:i + 2]))
            i += 2
    return result
    

def prepare_template(tgt_params):
    """Creates target projstring template and list of initial values"""
    template = ''
    initial_values = []
    for name, value in tgt_params.items():
        if name.startswith('+'):
            template += name
            if len(value) > 0:
                template += '='
                subvalues = []
                var_count = 0
                for subval in value:
                    if isinstance(subval, (float, int, long)):
                        subvalues.append(
                            '{' + str(len(initial_values)) + '}')
                        initial_values.append(subval)
                        var_count += 1
                    else:
                        subvalues.append(subval)
                template += ','.join(subvalues)
            template += ' '
    return template, initial_values


def find_params(src_proj, tgt_params, points):
    """Finds unknown parameters of target projection
    using least squares method
    """
    src_srs = osr.SpatialReference()
    src_srs.ImportFromProj4(to_str(src_proj))
    tgt_template, initial_values = prepare_template(tgt_params)
    proj_param_count = len(initial_values)
    # Modifiers are numeric parameters that are not part of Proj4 syntax
    modifiers = { '--k_0': 1.0, '--x_0': 0.0, '--y_0': 0.0, '--z_0': 0.0, }
    unknown_modifiers = []
    for name, value in tgt_params.items():
        if not name.startswith('+'):
            modifiers[name] = float(value[0])
            if isinstance(value[0], float):
                unknown_modifiers.append(name)
                initial_values.append(value[0])
    
    def target(xs):
        """Target function"""
        tgt_proj = tgt_template.format(*xs[:proj_param_count])
        tgt_srs = osr.SpatialReference()
        tgt_srs.ImportFromProj4(to_str(tgt_proj))
        m = modifiers.copy()
        for i, mod_name in enumerate(unknown_modifiers):
            m[mod_name] = xs[proj_param_count + i]
        return calc_residuals(src_srs, tgt_srs, m, points)
    
    # If all parameters are known, calculate the residuals
    if not initial_values:
        tgt_srs = tgt_srs = osr.SpatialReference()
        tgt_srs.ImportFromProj4(to_str(tgt_template))
        residuals = calc_residuals(src_srs, tgt_srs, modifiers, points)
        return (
            refine_projstring(tgt_template),
            modifiers,
            group_residuals(residuals, points)
            )
    # Solving the problem
    x, cov_x, infodict, mesg, ier = leastsq(
        target, initial_values, ftol=1e-12, full_output=True)
    # Formatting outputs
    if ier not in (1, 2, 3, 4):
        return None, None, None
    result_projstring = refine_projstring(tgt_template.format(*x))
    fvec = infodict['fvec']
    residuals = group_residuals(fvec, points)
    for i, mod_name in enumerate(unknown_modifiers):
        modifiers[mod_name] = x[proj_param_count + i]
    return result_projstring, modifiers, residuals


def parse_arguments(argv):
    """Parses command line arguments of the program
    and returns source projection Proj4 string,
    dict of target projection parameters, and input filename (or file object).
    Each parameter is represented as a list of subparameters
    which may be strings(known parameters) or floats (unknown ones).
    """
    tgt_option_re = re.compile(r'^(--[kxyz]_0)(=|~|=~)(.*)$')
    param_re = re.compile(r'^(\+[0-9a-zA-Z_]+)=?(.*)$')
    src_params = []
    options, tgt_params = {}, {}
    input_file = None
    src_parsing_mode = True
    for arg in argv[1:]:
        if hasattr(arg, '__iter__') and not isinstance(arg, (bytes, unicode)):
            # Can accept iterable object instead of filename
            if input_file:
                raise ValueError('Multiple input files are not supported')
            input_file = arg
            continue
        arg = to_unicode(arg, sys.getfilesystemencoding())
        if arg.startswith('-'):
            m = tgt_option_re.match(arg)
            if m: # The option changes target function behavior
                pname, delimiter, pvalue = m.groups()
                pknown = delimiter == '='
                tgt_params[pname] = [pvalue] if pknown else [float(pvalue)]
            else: # The option doesn't changes target function behavior
                splitarg = arg.split('=', 1)
                if len(splitarg) == 2:
                    options[splitarg[0]] = splitarg[1]
                else:
                    options[arg] = True
        elif src_parsing_mode:
            if arg == '+to': # End of source projection parameters
                src_parsing_mode = False
            elif arg.startswith('+'): # Source projection parameter
                src_params.append(arg)
            else:
                raise ValueError('Unexpected token: {0}'.format(arg))
        else: # Target projection parameters
            if arg.startswith('+'): # Target projection parameter
                m = param_re.match(arg)
                if not m:
                    raise ValueError('Invalid parameter: {0}'.format(arg))
                pname, pvalue = m.groups()
                if pvalue:
                    subvalues = pvalue.split(',')
                    tgt_params[pname] = [
                        float(v[1:]) if v.startswith('~') else v
                        for v in subvalues]
                else:
                    tgt_params[pname] = []
            else: # File name
                if input_file:
                    raise ValueError('Multiple input files are not supported')
                input_file = arg
    if src_params:
        src_proj = ' '.join(src_params)
    else:
        src_proj = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
    return src_proj, tgt_params, options, input_file


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


def read_points_from_iterable(fp):
    """Reads points from an iterable of strings"""
    points = []
    for line in fp:
        u_line = to_unicode(line, 'utf-8')
        tokens = u_line.strip().split()
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
        tokens = u_line.strip().split(None, number_count)
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
    

def read_points(textfile, encoding='utf-8'):
    """Reads points from a file"""
    if isinstance(textfile, (bytes, unicode)):
        with codecs.open(textfile, 'r', encoding) as fp:
            return read_points_from_iterable(fp)
    return read_points_from_iterable(textfile)


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


def format_extra_params(modifiers):
    """Returns extra parameters as a text string"""
    items = list(modifiers.items())
    items.sort()
    return 'Extra transform: ' + ', '.join('{0}: {1}'.format(*i) for i in items)


def to_wkt(projstring, esri=False, pretty=False):
    """Returns projection parameters as well-known text"""
    srs = osr.SpatialReference()
    srs.ImportFromProj4(to_str(projstring))
    if esri:
        srs.MorphToESRI()
    return srs.ExportToPrettyWkt() if pretty else srs.ExportToWkt()


def to_mapinfo(projstring):
    """Returns projection parameters as MapInfo CoordSys definition"""
    srs = osr.SpatialReference()
    srs.ImportFromProj4(to_str(projstring))
    return srs.ExportToMICoordSys()


def generate_output(
        outfile, result_projstring, extra_params, options, points, residuals):
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
        outfile.write(format_extra_params(extra_params))
        outfile.write('\n')
        outfile.write(format_residuals(points, residuals))
    outfile.write('\n')


def arg_main(argv, outfile):
    """The variant of main() that expects sys.argv and sys.stdout
    as function arguments (for use in tests or wrapper scripts)
    """
    src_proj, tgt_params, options, input_file = parse_arguments(argv)
    if '-h' in options or '--help' in options:
        outfile.write(usage_help(argv[0]))
        outfile.write('\n')
        return 0
    encoding = options.get('--encoding', 'utf-8')
    points = read_points(input_file, encoding)
    result_projstring, extra_params, residuals = find_params(
        src_proj, tgt_params, points)
    if result_projstring:
        generate_output(outfile, result_projstring, extra_params,
                        options, points, residuals)
        return 0
    else:
        if not(set(options.keys()) &
               set(['--proj', '--proj4', '--wkt', '--esri', '--mapinfo'])):
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
