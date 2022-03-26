'''
    ModernGL extension for storing mesh data
    [andreika]: Modified to support vertex colors instead of texture coords
'''

import logging
import re
import struct

from pyrr import aabb


log = logging.getLogger('ModernGL.ext.obj')

RE_COMMENT = re.compile(r'#[^\n]*\n', flags=re.M)
RE_VERT = re.compile(r'^v\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)$')
RE_COLOR = re.compile(r'^vc\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)(?:\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?))?$')
RE_NORM = re.compile(r'^vn\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)$')
RE_FACE = re.compile(r'^f\s+(\d+)(/(\d+)?(/(\d+))?)?\s+(\d+)(/(\d+)?(/(\d+))?)?\s+(\d+)(/(\d+)?(/(\d+))?)?$')

PACKER = 'lambda vx, vy, vz, cx, cy, cz, nx, ny, nz: struct.pack("%df", %s)'


def default_packer(vx, vy, vz, cx, cy, cz, nx, ny, nz):
    return struct.pack('9f', vx, vy, vz, cx, cy, cz, nx, ny, nz)


def int_or_none(x):
    return None if x is None else int(x)


def safe_float(x):
    return 0.0 if x is None else float(x)


class Mesh:
    def __init__(self, vert, color, norm, face):
        self.vert = vert
        self.color = color
        self.norm = norm
        self.face = face
        # we need AABB to zoom in the model
        self.aabb = aabb.create_zeros()

    def pack(self, packer=default_packer) -> bytes:
        '''
            Args:
                packer (str or lambda): The vertex attributes to pack.

            Returns:
                bytes: The packed vertex data.

            Examples:

                .. code-block:: python

                    import ModernGL
                    from ModernGL.ext import obj

                    model = obj.Obj.open('box.obj')

                    # default packer
                    data = model.pack()

                    # same as the default packer
                    data = model.pack('vx vy vz tx ty tz nx ny nz')

                    # pack vertices
                    data = model.pack('vx vy vz')

                    # pack vertices and texture coordinates (xy)
                    data = model.pack('vx vy vz tx ty')

                    # pack vertices and normals
                    data = model.pack('vx vy vz nx ny nz')

                    # pack vertices with padding
                    data = model.pack('vx vy vz 0.0')
        '''

        if isinstance(packer, str):
            nodes = packer.split()
            packer = eval(PACKER % (len(nodes), ', '.join(nodes)))

        result = bytearray()

        for v, t, n in self.face:
            vx, vy, vz = self.vert[v - 1]
            cx, cy, cz = self.color[t - 1] if t is not None else (0.0, 0.0, 0.0)
            nx, ny, nz = self.norm[n - 1] if n is not None else (0.0, 0.0, 0.0)
            result += packer(vx, vy, vz, cx, cy, cz, nx, ny, nz)

        return bytes(result)
