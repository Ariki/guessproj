guessproj:  Guessing parameters of cartographic projection
==========================================================

``guessproj`` is a Python script that calculates unknown parameters
of cartographic projection or coordinate system from coordinates
of identical points in some known coordinate system and in unknown one.
You should know projection type, though.
The script can also determine parameters of transformation between two datums.

The script uses ``pyproj`` and ``scipy`` internally.
The method of least squares is used, so the more points you have,
the better accuracy will be achieved.

Supported Python versions
-------------------------

Python 2.6+ and 3.3+ are supported. The script is written in pure Python
itself but depends on some packages that are not.

Installation
------------

The best way to install ``guessproj`` is using
`pip <https://pip.pypa.io/en/latest/quickstart.html>`_::

    pip install guessproj
    
Be aware that ``guessproj`` has some binary dependencies that you need
to install before trying to install ``guessproj``.
These are `GDAL`_ and `PROJ.4`_.
If you are a GIS specialist you probably already have these libraries.
You also need Python bindings for them (`GDAL bindings`_ and `pyproj`_)
as well as `NumPy`_ and `SciPy`_ packages.
The ``pip`` tool will try to install these packages automatically
but on most systems you'll need to install them in a platform-specific way.

Note that GDAL is an optional dependency but may become required in future
versions of ``guessproj``.

Instead of using ``pip``, you can download the source archive,
unpack it and run ::

    python setup.py install
    
in the unpacked directory. You need `setuptools`_ to do this.

Also, you can use ``guessproj`` without installation. Just download
the file `guessproj.py`_ and run it like any Python script::

    python guessproj.py --help
    
You still need dependencies to be installed, of course.

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

Obviously, the number of point coordinate values must be not less
than the number of unknown parameters to determine.

Both decimal format and degrees, minutes and seconds format
(``XXXdXX'XX.XXX"``) are supported for coordinate values.
You can use comma as well as period to separate fractional part.

Command line  syntax
--------------------

Command line syntax used to run the script is similar to that of ``cs2cs``
utility which comes with ``PROJ.4`` library. You should specify parameters
of known coordinate system in ``PROJ.4`` format (referred as projstring here),
known and unknown parameters of the unknown system, and a path to input file.
Exact parameters of various coordinate systems you can find
in `PROJ.4 documentation`_.

The unknown parameters are specified among all others in the projstring,
the only difference is using ``~`` symbol instead of ``=``. The numeric value
that follows the ``~`` symbol is an initial approximation of the parameter value.
For ``+towgs84`` parameter, you can specify ``~`` before any (or all) of comma-separated
values. The combination ``=~`` is the same as ``~``.

Example::

    guessproj +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs +to \
      +proj=tmerc +ellps=krass +lat_0=0 +lon_0~44 +x_0=300000 +y_0~-4.7e6 \
      +towgs84=23.57,-140.95,-79.8,0,-0.35,-0.79,-0.22 points.txt

All that goes before ``+to`` argument is a projstring for the known system
(if omitted, WGS84 longitude/latitude is used by default). All the rest
parameters starting with ``+`` are the projstring for the unknown system,
where initial approximations of the unknown parameters are marked with ``~``.
In this example, parameters ``+lon_0`` and ``+y_0`` are unknown. The last argument
is a name of input text file containing point coordinates.

The script can evaluate numeric parameters only, so you should specify
at least ``+proj`` and ``+ellps``. It's worth mentioning, also, that some
parameters have the same (or nearly the same) effect, so it's a bad idea,
for example, to specify both ``+lat_0`` and ``+y_0`` as unknown
for Transverse Mercator projection. The system of equations will be
ill-determined in that case.

If no unknown parameters specified, the script will just transform the points
and calculate residual errors for each coordinate value.

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
(experimental, GDAL Python bindings required).

Option ``--pretty`` forces pretty WKT formatting when used with ``--wkt``
or ``--esri``.

Option ``--mapinfo`` forces output of projection parameters in MapInfo CoordSys
format (experimental, GDAL Python bindings required). Be aware that current
GDAL based implementation does not handle datum and ellipsoid parameters
correctly.

Output
------

The default output of the program is a projstring in which approximated values
of parameters are replaced with the exact values found by the script,
and a list of residual errors for each point. Other forms of output
can be specified using program options.

If GDAL bindings are installed, the projstring will be formatted
so as to be represented in a normalized form.

Testing
-------

To run unit tests with Python 2.7 or 3.3+, execute in source directory::

    python -m unittest discover test
    
In Python 2.6, you should install unittest2 package and use::

    PYTHONPATH=. unit2 discover test
    
You can also run scripts from ``test/`` directory directly.


.. _GDAL: http://www.gdal.org/
.. _PROJ.4: http://trac.osgeo.org/proj/
.. _GDAL bindings: https://pypi.python.org/pypi/GDAL/
.. _pyproj: https://pypi.python.org/pypi/pyproj/
.. _NumPy: https://pypi.python.org/pypi/numpy/
.. _SciPy: https://pypi.python.org/pypi/scipy/
.. _setuptools: https://pypi.python.org/pypi/setuptools/
.. _guessproj.py: https://raw.githubusercontent.com/Ariki/guessproj/master/guessproj.py
.. _PROJ.4 documentation: https://trac.osgeo.org/proj/wiki/GenParms
