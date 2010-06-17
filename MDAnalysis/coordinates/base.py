"""
:mod:`MDAnalysis.coordinates.base --- base classes
==================================================

Derive other Reader and Writer classes from the classes in this module.

.. autoclass:: Timestep
   :members:

.. autoclass:: IObase
   :members:

.. autoclass:: Reader
   :members:

.. autoclass:: Writer
   :members:
"""

import numpy
import MDAnalysis.core
from MDAnalysis.core import units, flags

class Timestep(object):
    """Timestep data for one frame

    Data:     numatoms                   - number of atoms
              frame                      - frame number
              dimensions                 - system box dimensions (x, y, z, alpha, beta, gamma)

    Methods:  t = Timestep(numatoms) - create a timestep object with space for numatoms (done automatically)
              t[i]                   - return coordinates for the i'th atom (0-based)
              t[start:stop:skip]     - return an array of coordinates, where start, stop and skip correspond to atom indices (0-based)
    """
    def __init__(self, arg):
        if numpy.dtype(type(arg)) == numpy.dtype(int):
            self.frame = 0
            self.numatoms = arg
            self._pos = numpy.zeros((self.numatoms, 3), dtype=numpy.float32, order='F')
            #self._pos = numpy.zeros((3, self.numatoms), numpy.float32)
            self._unitcell = numpy.zeros((6), numpy.float32)
        elif isinstance(arg, Timestep): # Copy constructor
            # This makes a deepcopy of the timestep
            self.frame = arg.frame
            self.numatoms = arg.numatoms
            self._unitcell = numpy.array(arg._unitcell)
            self._pos = numpy.array(arg._pos)
        elif isinstance(arg, numpy.ndarray):
            if len(arg.shape) != 2: raise ValueError("numpy array can only have 2 dimensions")
            self._unitcell = numpy.zeros((6), numpy.float32)
            self.frame = 0
            if arg.shape[0] == 3: self.numatoms = arg.shape[0]  # ??? is this correct ??? [OB]
            else: self.numatoms = arg.shape[-1]                 # ??? reverse ??? [OB]
            self._pos = arg.copy('Fortran')
        else: raise ValueError("Cannot create an empty Timestep")
        self._x = self._pos[:,0]
        self._y = self._pos[:,1]
        self._z = self._pos[:,2]
    def __getitem__(self, atoms):
        if numpy.dtype(type(atoms)) == numpy.dtype(int):
            if (atoms < 0):
                atoms = self.numatoms + atoms
            if (atoms < 0) or (atoms >= self.numatoms):
                raise IndexError
            return self._pos[atoms]
        elif type(atoms) == slice or type(atoms) == numpy.ndarray:
            return self._pos[atoms]
        else: raise TypeError
    def __len__(self):
        return self.numatoms
    def __iter__(self):
        def iterTS():
            for i in xrange(self.numatoms):
                yield self[i]
        return iterTS()
    def __repr__(self):
        return "< Timestep "+ repr(self.frame) + " with unit cell dimensions " + repr(self.dimensions) + " >"
    def copy(self):
        return self.__deepcopy__()
    def __deepcopy__(self):
        # Is this the best way?
        return Timestep(self)

    @property
    def dimensions(self):
        """unitcell dimensions (A, B, C, alpha, beta, gamma)"""
        # Layout of unitcell is [A, alpha, B, beta, gamma, C]
        return numpy.take(self._unitcell, [0,2,5,1,3,4])

class IObase(object):
    """Base class bundling common functionality for trajectory I/O.    
    """
    #: override to define trajectory format of the reader/writer (DCD, XTC, ...)
    format = None

    #: dict with units of of *time* and *length* (and *velocity*, *force*, 
    #: ... for formats that support it)
    units = {'time': None, 'length': None}

    # could cache f or compute at __init_ ...
    def convert_pos_from_native(self, x):
        """In-place conversion of coordinate array x from native units to base units."""
        f = units.get_conversion_factor('length', self.units['length'], MDAnalysis.core.flags['length_unit'])
        x *= f
        return x

    def convert_time_from_native(self, t):
        """Convert time *t* from native units to base units."""
        f = units.get_conversion_factor('time', self.units['time'], MDAnalysis.core.flags['time_unit'])
        t *= f
        return t

    def convert_pos_to_native(self, x):
        """In-place conversion of coordinate array x from base units to native units."""
        f = units.get_conversion_factor('length', MDAnalysis.core.flags['length_unit'], self.units['length'])
        x *= f
        return x

    def convert_time_from_native(self, t):
        """Convert time *t* from base units to native units."""
        f = units.get_conversion_factor('time', MDAnalysis.core.flags['time_unit'], self.units['time'])
        t *= f
        return t

    def close_trajectory(self):
        pass

class Reader(IObase):
    """Base class for trajectory readers.

    See Trajectory API definition in :mod:`MDAnalysis.coordinates` for
    the required attributes and methods.
    """

    #: supply the appropriate Timestep class, e.g. 
    #: :class:`MDAnalysis.coordinates.xdrfile.XTC.Timestep` for XTC
    _Timestep = Timestep

    def __len__(self):
        return self.numframes

    def next(self):
        """Forward one step to next frame."""
        return self._read_next_timestep()

    def rewind(self):
        """Position at beginning of trajectory"""
        self[0]

    def __repr__(self):
        return "< %s %r with %d frames of %d atoms (%d fixed) >" % \
            (self.__class__.__name__, self.filename, self.numframes, self.numatoms, self.fixed)


    # def _read_next_timestep(self, ts=None)
    # def __del__(self)
    # def __iter__(self):

class Writer(IObase):
    """Base class for trajectory writers.

    See Trajectory API definition in :mod:`MDAnalysis.coordinates` for
    the required attributes and methods.
    """

    def __del__(self):
        self.close_trajectory()

    def __repr__(self):
        return "< %s %r for %d atoms >" % (self.__class__.__name__, self.filename, self.numatoms)

    # def write_next_timestep(self, ts=None)
