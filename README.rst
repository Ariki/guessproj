guessproj:  Guessing parameters of cartographic projection
==========================================================

``guessproj.py`` is a Python script that finds out unknown parameters
of cartographic projection or coordinate system from coordinates
of identical points in some known coordinate system and in unknown one.
You should know projection type, though.
The script can also determine parameters of transformation between two datums.

The script uses ``pyproj`` and ``scipy`` to do its work.
The method of least squares is used, so the more points you have, the better
accuracy will be achieved.

Supported Python versions
-------------------------

Python 2.7 and 3.3+ are supported. It may work on other versions but not tested.
The script is cross-platform. It's pure python itself but depends
on some libraries that are not.

Input data format
-----------------

The input data for the script is a text file that contains lines
of space separated values, each line representing a point.

Input data format for 2D points is as follows::

    x1 y1 x2 y2 point name

Input data format for 3D points is as follows::

    x1 y1 z1 x2 y2 z2 point name

Point name may contain spaces but should not start with a number.
If the line starts with ``#``, it will be ignored.

The coordinates in known coordinate system go first, followed by coordinates
in unknown one. 3D points are mostly useful if there exists
a datum transformation between coordinate systems.

Obviously, the number of points must be not less than the number of unknown
parameters to determine.

Both decimal format and degrees, minutes and seconds format
(``XXXdXX'XX.XXX"``) are supported for coordinate values.
You can use comma instead of period to separate fractional part.

Command line  syntax
--------------------

Command line syntax used to run the script is similar to that of ``cs2cs``
utility which comes with ``proj4`` library. You should specify parameters
of known coordinate system in projstring format, known and unknown parameters
of the unknown system, and a path to input file. Exact parameters of various
coordinate systems you can find in ``proj4`` documentation.

The unknown parameters are specified among all others in the projstring,
the only difference is using ``~`` symbol instead of ``=``. The numeric value
that follows the ``~`` symbol is an initial approximation of the parameter value.
For ``+towgs84`` parameter, you can specify ``~`` before any (or all) of comma-separated
values. The combination ``=~`` is the same as ``~``.

Example::

    guessproj.py +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs +to \
      +proj=tmerc +ellps=krass +lat_0=0 +lon_0~44 +x_0=300000 +y_0~-4.7e6 \
      +towgs84=23.57,-140.95,-79.8,0,-0.35,-0.79,-0.22 points.txt

All that goes before ``+to`` argument is a projstring for the known system
(if omitted, WGS84 longitude/latitude is used by default). All the rest
parameters starting with ``+`` are the projstring for the unknown system,
where initial approximations of the unknown parameters are marked with ``~``.
In this example, parameters ``+lon_0`` and ``+y_0`` are unknown. The last argument
is a name of input text file containing point coordinates.

The script can evaluate only numeric parameters, so you should specify
at least ``+proj`` and ``+ellps``. It's worth mentioning, also, that some
parameters have the same (or nearly the same) effect, so it's a bad idea,
for example, to specify both ``+lat_0`` and ``+y_0`` as unknown
for Transverse Mercator projection. The system of equations will be
ill-determined.

Options
-------

Any additional program options (which are not part of projstring syntax)
start with ``-`` or ``--``.

Option ``-h`` or ``--help`` prints a short command line reference and exits
the program.

Option ``--encoding=ENCODING_NAME`` specifies the encoding of input file
(``--encoding=utf-8`` by default).

Option ``--proj`` or ``--proj4`` forces output of resulting projstring only,
suppressing table of residual errors.

Option ``--wkt`` forces output of projection parameters in OGC WKT format
(GDAL Python bindings required).

Option ``--esri`` forces output of projection parameters in Esri WKT format
(experimental, GDAL Python bindings required)

Option ``--pretty`` forces pretty WKT formatting when used with ``--wkt``
or ``--esri``.

Output
------

The default output of the program is a projstring in which approximated values
of parameters are replaced with exact values determined by the script,
and a list of residual errors for each point.

