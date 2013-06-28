'''
This module provides a class function decorator to cache the results for functions. I have found that parsing the files to get energy, forces, stresses, etc... is slow when you have to loop through hundreds or thousands of files. So, we are going to try caching the results.


It is not clear this will work all the reading seems to be done in restart_load. I that is true, memoizing these functions will have no effect. there needs to be a redesign to only get data when you want it, e.g. lazy evaluation.

the key might be caching the read functions

    def read_outcar(self):
        # Spin polarized calculation?
        file = open('OUTCAR', 'r')
        lines = file.readlines()
        file.close()
        for line in lines:
            if line.rfind('ISPIN') > -1:
                if int(line.split()[2])==2:
                    self.spinpol = True
                else:
                    self.spinpol = None
        self.energy_free, self.energy_zero = self.read_energy()
        self.forces = self.read_forces(self.atoms)
        self.dipole = self.read_dipole()
        self.fermi = self.read_fermi()
        self.stress = self.read_stress()
        self.nbands = self.read_nbands()
        self.read_ldau()
        p=self.int_params
        q=self.list_params
        if self.spinpol:
            self.magnetic_moment = self.read_magnetic_moment()
            if p['lorbit']>=10 or (p['lorbit']!=None and q['rwigs']):
                self.magnetic_moments = self.read_magnetic_moments(self.atoms)
            else:
                self.magnetic_moments = None
        self.set(nbands=self.nbands)

read_outcar does not return anything, so it cannot be cached. It sets lots of attributes. the get functions return these attributes, they do not read the files.

this function itself should have the spin-polarized reading factored out so that a read_spinpol function returns
self.spinpol = self.read_spinpol()

then we could cache:
self.read_spinpol
self.read_energy
self.read_forces
self.read_fermi
self.read_stress
self.read_nbands
self.read_magnetic_moment

which ought to avoid reading outcar again
'''

def read_spinpol(self):
    'read OUTCAR and return if calculation was spin-polarized'
    with open('OUTCAR') as f:
        for line in f:
            if line.rfind('ISPIN') > -1:
                if int(line.split()[2])==2:
                    return  True
                else:
                    return None

from functools import wraps
import os, pickle
from jasp import *

def persistent_memoize(func):
    '''function decorator to provide a persistent cache mechanism for jasp'''
    if os.path.exists('CACHE'):
        with open('CACHE') as f:
            cache = pickle.load(f)
        else:
            cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # dictionaries are not hashable, so we use the pickle string
        # as the key.
        key = pickle.dumps((args, kwargs))


        if key not in cache:
            cache[key] = func(*args, **kwargs)
            with open('CACHE', 'wb') as f:
                pickle.dump(cache, f)
        return cache[key]
    return wrapper


Vasp.get_potential_energy = persistent_memoize(Vasp.get_potential_energy)
Vasp.get_forces = persistent_memoize(Vasp.get_forces)
Vasp.get_stress = persistent_memoize(Vasp.get_stress)
