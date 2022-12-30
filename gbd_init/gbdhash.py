# GBD Benchmark Database (GBD)
# Copyright (C) 2021 Markus Iser, Karlsruhe Institute of Technology (KIT)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import io
import hashlib

from gbd_core.util import open_cnf_file

try:
    from gbdc import gbdhash as gbd_hash
except ImportError:
    try:
        from gbdhashc import gbdhash as gbd_hash
    except ImportError:
        def gbd_hash(filename):
            file = open_cnf_file(filename, 'rb')
            buff = io.BufferedReader(file, io.DEFAULT_BUFFER_SIZE * 16)

            space = False
            skip = False
            start = True
            cldelim = True
            hash_md5 = hashlib.md5()

            for byte in iter(lambda: buff.read(1), b''):
                if not skip and (byte >= b'0' and byte <= b'9' or byte == b'-'):
                    cldelim = byte == b'0' and (space or start)
                    start = False
                    if space:
                        space = False
                        hash_md5.update(b' ')
                    hash_md5.update(byte)
                elif byte <= b' ':
                    space = not start # remember non-leading space characters 
                    skip = skip and byte != b'\n' and byte != b'\r' # comment line ended
                else: #byte == b'c' or byte == b'p':
                    skip = True  # do not hash comment and header line

            if not cldelim:
                hash_md5.update(b' 0')

            file.close()

            return hash_md5.hexdigest()