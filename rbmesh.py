# The MIT License (MIT)
#
# 	Copyright (c) 2019 Sergey Makeev
#
# 	Permission is hereby granted, free of charge, to any person obtaining a copy
# 	of this software and associated documentation files (the "Software"), to deal
# 	in the Software without restriction, including without limitation the rights
# 	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# 	copies of the Software, and to permit persons to whom the Software is
# 	furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
# 	all copies or substantial portions of the Software.
#
# 	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# 	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# 	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# 	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# 	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# 	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# 	THE SOFTWARE.
import io
import struct
import logger
import fbx


class Vertex:
    def __init__(self, px, py, pz, nx, ny, nz, u, v, w, r, g, b, a):
        self.p_x = px
        self.p_y = py
        self.p_z = pz
        self.n_x = nx
        self.n_y = ny
        self.n_z = nz
        self.u = u
        self.v = v
        self.w = w
        self.r = r
        self.g = g
        self.b = b
        self.a = a


class Triangle:
    def __init__(self, i0, i1, i2):
        self.i0 = i0
        self.i1 = i1
        self.i2 = i2


class Mesh:
    def __init__(self):
        self.vertices = []
        self.triangles = []
        self.lod_data = []
        self.min_x = 99999999.0
        self.min_y = 99999999.0
        self.min_z = 99999999.0
        self.max_x = -99999999.0
        self.max_y = -99999999.0
        self.max_z = -99999999.0

    def append_vertex(self, vrx):
        self.min_x = min(self.min_x, vrx.p_x)
        self.min_y = min(self.min_y, vrx.p_y)
        self.min_z = min(self.min_z, vrx.p_z)
        self.max_x = max(self.max_x, vrx.p_x)
        self.max_y = max(self.max_y, vrx.p_y)
        self.max_z = max(self.max_z, vrx.p_z)
        self.vertices.append(vrx)

    def append_triangle(self, idx):
        self.triangles.append(idx)

    def assign_lod_data(self, lod_data):
        if len(lod_data) == 2 and lod_data[0] == 0 and lod_data[1] == 0:
            self.lod_data = [0, len(self.triangles)]
        else:
            self.lod_data = lod_data

    def get_number_of_lods(self):
        return len(self.lod_data)-1


#
# https://developer.roblox.com/articles/Roblox-Mesh-Format
#
# version 1.00
#
# This is the original version of Roblox's mesh format, which is stored purely in ASCII and can be read by humans.
# These files are stored as 3 lines of text:
#
# version 1.00
# num_faces
# data
#
# The num_faces line represents the number of polygons to expect in the data line.
# The data line represents a series of concatenated Vector3 pairs, stored inbetween brackets with the XYZ coordinates
# separated with commas as so: [1.00,1.00,1.00]
#
# You should expect to see num_faces * 9 concatenated Vector3 pairs in this line.
# Every single vertex is represented in the following manner:
# [vX,vY,vZ][nX,nY,nZ][tU,tV,tW]
#
# The 1st pair, [vX,vY,vZ] is the location of the vertex point. In version 1.00, the XYZ values are doubled,
#    so you should scale the values down by 0.5 when converting them to floats. This issue is fixed in version 1.01.
# The 2nd pair, [nX,nY,nZ] is the normal unit vector of the vertex point, which is used to determine how light
#    bounces off of this vertex.
# The 3rd pair, [tU,tV,tW] is the 2D UV texture coordinate of the vertex point, which is used to determine how the
#    mesh's texture is applied to the mesh. The tW coordinate is unused, so you can expect it's value to be zero.
#    One important quirk to note is that the tV coordinate is inverted, so when converting it to a float and
#    storing it, the value should be stored as 1.f - tV.
#
# Every 3 sets of 3 Vector3 pairs are used to form a polygon, hence why you should expect to see num_faces * 9.
#
#
# version 2.00
# The version 2.00 format is a lot more complicated, as it's stored in a binary format and files may differ in
# structure depending on factors that aren't based on the version number. You will need some some advanced knowledge in
# Computer Science to understand this portion of the article. This will be presented in a C syntax.
#
# MeshHeader
# After reading past the version 2.00\n text, the first chunk of data can be represented with the following struct:
#
# struct MeshHeader
# {
# unsigned short sizeofMeshHeader; // Used to verify your MeshHeader struct is the same as this file's MeshHeader struct
# unsigned char sizeofMeshVertex; // Used to verify your MeshVertex struct is the same as this file's MeshVertex struct
# unsigned char sizeofMeshFace; // Used to verify your MeshFace struct is the same as this file 's MeshFace struct
# unsigned int num_vertices; // The number of vertices in this mesh
# unsigned int num_faces; // The number of faces in this mesh
# }
#
# One critical quirk to note, is that sizeofMeshVertex can vary between 36 and 40 bytes, due to the introduction of
# vertex color data to newer meshes. If you don't account for this difference, the mesh may not be read correctly.
#
# MeshVertex
#
# Once you have read the MeshHeader, you should expect to read an array, MeshVertex[num_vertices] vertices;
# using the following struct:
#
# struct MeshVertex
# {
#   float vx, vy, vz; // XYZ coordinate of the vertex
#   float nx, ny, nz; // XYZ coordinate of the vertex's normal
#   float tu, tv, tw; // UV coordinate of the vertex(tw is reserved)
#
#   // WARNING: The following bytes only exist if 'MeshHeader.sizeofMeshVertex' is equal to 40, rather than 36.
#   unsigned char r, g, b, a; // The RGBA color of the vertex
# }
#
# This array represents all of the vertices in the mesh, which can be linked together into faces.
#
# MeshFace
#
# Finally, you should expect to read an array, MeshFace[num_faces] faces; using the following struct:
# struct MeshFace
# {
# 	unsigned int a; // 1st Vertex Index
# 	unsigned int b; // 2nd Vertex Index
# 	unsigned int c; // 3rd Vertex Index
# }
#
# This array represents indexes in the MeshVertex array that was noted earlier.
# The 3 MeshVertex structs that are indexed using the MeshFace are used to form a polygon in the mesh.
#
#
#
#
# version 3.00 (undocumented)
#
# https://devforum.roblox.com/t/version-3-00-of-mesh-format-has-no-public-documentation/287887
# The changes to the format are actually quite minor.
#
# Firstly, here are the changes to the MeshHeader:
#
# struct MeshHeader
# {
# 	short sizeof_MeshHeader;
# 	short sizeof_MeshVertex;
# 	short sizeof_MeshFace;
# [+]	short sizeof_MeshLOD;
#
# [+]	short numLODs;
# 	short numVerts;
# 	short numFaces;
# }
#
# After reading the faces of the mesh file, there will be (numLODs * 4) bytes at the end of the file,
# representing an array of numLODs ints, or just:
#
# int mesh_LODs[numLODs];
#
# The array uses integers because sizeof_MeshLOD should always have a value of 4 to be considered valid.
#
# The mesh_LODs array represents a series of face ranges, the faces of which form meshes that can be used at various
# distances by Roblox’s mesh rendering system.
#
# For example, you might have an array that looks like this:
#
# { 0, 1820, 2672, 3045 }
#
# This values in this array are interpreted as follows:
#
#     The Main mesh is formed using faces [0 - 1819]
#     The 1st LOD mesh is formed using faces [1820 - 2671]
#     The 2nd LOD mesh is formed using faces [2672 - 3044]
#
# All of these faces should be stored in whatever array of MeshFaces you have defined.
#


# noinspection PyUnusedLocal
def parse_mesh(content: bytes) -> Mesh or None:
    data_stream = io.BytesIO(content)
    header = data_stream.read(12)

    mesh = Mesh()

    if header == b'version 1.00' or header == b'version 1.01':
        scale = 1.0
        if header == b'version 1.00':
            scale = 0.5
        # skip line
        data_stream.readline()
        num_faces = int(data_stream.readline())
        text_data = data_stream.readline()
        text_data = text_data.replace(b'][', b';')
        text_data = text_data.replace(b'[', b'')
        text_data = text_data.replace(b']', b'')
        pairs = text_data.split(b';')
        pairs_count = len(pairs)
        # print(str(pairs_count))
        if pairs_count != (num_faces * 9):
            logger.fatal("Invalid number of pairs")
            return None

        for i in range(0, pairs_count, 3):
            values = pairs[i + 0].split(b',')
            if len(values) != 3:
                logger.fatal("Invalid number of values")
                return None
            pos_x = float(values[0]) * scale
            pos_y = float(values[1]) * scale
            pos_z = float(values[2]) * scale

            values = pairs[i + 1].split(b',')
            if len(values) != 3:
                logger.fatal("Invalid number of values")
                return None
            nrm_x = float(values[0])
            nrm_y = float(values[1])
            nrm_z = float(values[2])

            values = pairs[i + 2].split(b',')
            if len(values) != 3:
                logger.fatal("Invalid number of values")
                return None
            t_u = float(values[0])
            t_v = float(values[1]) * -1.0
            t_w = float(values[2])

            vrx = Vertex(pos_x, pos_y, pos_z, nrm_x, nrm_y, nrm_z, t_u, t_v, t_w, 1, 1, 1, 1)
            mesh.append_vertex(vrx)

        for i in range(0, num_faces):
            tri = Triangle(i * 3 + 0, i * 3 + 1, i * 3 + 2)
            mesh.append_triangle(tri)

        mesh.assign_lod_data([0, num_faces])

        return mesh

    mesh_version = 0
    # binary mesh
    if header == b'version 2.00':
        mesh_version = 2

    # binary mesh with LODs
    if header == b'version 3.00' or header == b'version 3.01':
        mesh_version = 3

    # binary mesh with LODs and skinning data
    if header == b'version 4.00' or header == b'version 4.01':
        mesh_version = 4

    # FACS animation added
    if header == b'version 5.00':
        mesh_version = 5

    # chunked format
    if header == b'version 6.00':
        mesh_version = 5

    if header == b'version 7.00':
        mesh_version = 5

    if mesh_version == 0:
        logger.fatal("Unsupported mesh header: " + str(header))
        return None

    # skip '\n'
    data_stream.read(1)

    sizeof_mesh_header = struct.unpack('H', data_stream.read(2))[0]

    sizeof_mesh_vertex = 0
    sizeof_mesh_face = 0
    num_vertices = 0
    num_faces = 0
    sizeof_mesh_lod = 0
    num_lods = 0
    num_joints = 0
    num_joint_name_chars = 0
    num_skinning_subsets = 0
    control_to_joint_driver_version = 0
    control_to_joint_driver_size = 0

    if mesh_version == 2:
        sizeof_mesh_vertex = struct.unpack('B', data_stream.read(1))[0]
        sizeof_mesh_face = struct.unpack('B', data_stream.read(1))[0]
        num_vertices = struct.unpack('I', data_stream.read(4))[0]
        num_faces = struct.unpack('I', data_stream.read(4))[0]
        if sizeof_mesh_header != 12:
            logger.fatal("Unsupported mesh v2 header size: " + str(sizeof_mesh_header))
            return None

    elif mesh_version == 3:
        sizeof_mesh_vertex = struct.unpack('B', data_stream.read(1))[0]
        sizeof_mesh_face = struct.unpack('B', data_stream.read(1))[0]
        sizeof_mesh_lod = struct.unpack('H', data_stream.read(2))[0]
        num_lods = struct.unpack('H', data_stream.read(2))[0]
        num_vertices = struct.unpack('I', data_stream.read(4))[0]
        num_faces = struct.unpack('I', data_stream.read(4))[0]
        if sizeof_mesh_header != 16:
            logger.fatal("Unsupported mesh v3 header size: " + str(sizeof_mesh_header))
            return None

    elif mesh_version == 4:
        # 0 - None, 1 - Unknown, 2 - RBX Simplifier, 3 - MeshOpt
        # noinspection PyUnusedLocal
        lod_type = struct.unpack('H', data_stream.read(2))[0]
        num_vertices = struct.unpack('I', data_stream.read(4))[0]
        num_faces = struct.unpack('I', data_stream.read(4))[0]
        num_lods = struct.unpack('H', data_stream.read(2))[0]
        sizeof_mesh_lod = 4
        num_joints = struct.unpack('H', data_stream.read(2))[0]
        num_joint_name_chars = struct.unpack('I', data_stream.read(4))[0]
        num_skinning_subsets = struct.unpack('H', data_stream.read(2))[0]
        # noinspection PyUnusedLocal
        num_quality_lods = struct.unpack('B', data_stream.read(1))[0]
        # skip padding
        data_stream.read(1)

        sizeof_mesh_vertex = 40
        sizeof_mesh_face = 12
        if sizeof_mesh_header != 24:
            logger.fatal("Unsupported mesh v4 header size: " + str(sizeof_mesh_header))
            return None
    elif mesh_version == 5:
        # 0 - None, 1 - Unknown, 2 - RBX Simplifier, 3 - MeshOpt
        # noinspection PyUnusedLocal
        lod_type = struct.unpack('H', data_stream.read(2))[0]
        num_vertices = struct.unpack('I', data_stream.read(4))[0]
        num_faces = struct.unpack('I', data_stream.read(4))[0]
        num_lods = struct.unpack('H', data_stream.read(2))[0]
        sizeof_mesh_lod = 4
        num_joints = struct.unpack('H', data_stream.read(2))[0]
        num_joint_name_chars = struct.unpack('I', data_stream.read(4))[0]
        num_skinning_subsets = struct.unpack('H', data_stream.read(2))[0]
        # noinspection PyUnusedLocal
        num_quality_lods = struct.unpack('B', data_stream.read(1))[0]
        # skip padding
        data_stream.read(1)

        control_to_joint_driver_version = struct.unpack('I', data_stream.read(4))[0]
        control_to_joint_driver_size = struct.unpack('I', data_stream.read(4))[0]

        sizeof_mesh_vertex = 40
        sizeof_mesh_face = 12
        if sizeof_mesh_header != 32:
            logger.fatal("Unsupported mesh v5 header size: " + str(sizeof_mesh_header))
            return None
    elif mesh_version == 6 or  mesh_version == 7:
        chunk_name = bytearray(8)
        data_stream.readinto(chunk_name)
        chunk_version = struct.unpack('I', data_stream.read(4))[0]
        chunk_size = struct.unpack('I', data_stream.read(4))[0]
        # chunk types
        # COREMESH v1(normal) / v2 (compressed)
        # LODS
        # SKINNING
        # FACS
        # HSRAVIS
        logger.fatal("Still WiP")
        return None
    else:
        logger.fatal("Unsupported mesh header: " + str(header))

    if num_vertices == 0 or num_faces == 0:
        logger.fatal("Empty mesh")
        return None

    if num_lods > 8:
        logger.fatal("Too many LODs. Broken file?")
        return None

    if sizeof_mesh_vertex != 36 and sizeof_mesh_vertex != 40:
        logger.fatal("Unsupported vertex size: " + str(sizeof_mesh_vertex))
        return None

    if sizeof_mesh_face != 12:
        logger.fatal("Unsupported face size: " + str(sizeof_mesh_face))
        return None

    if num_lods > 0:
        if sizeof_mesh_lod != 4:
            logger.fatal("Unsupported LOD header size: " + str(sizeof_mesh_lod))
            return None

    # read vertices
    for i in range(0, num_vertices):
        pos_x = struct.unpack('f', data_stream.read(4))[0]
        pos_y = struct.unpack('f', data_stream.read(4))[0]
        pos_z = struct.unpack('f', data_stream.read(4))[0]
        nrm_x = struct.unpack('f', data_stream.read(4))[0]
        nrm_y = struct.unpack('f', data_stream.read(4))[0]
        nrm_z = struct.unpack('f', data_stream.read(4))[0]
        t_u = struct.unpack('f', data_stream.read(4))[0]
        t_v = struct.unpack('f', data_stream.read(4))[0]
        t_w = struct.unpack('f', data_stream.read(4))[0]
        if sizeof_mesh_vertex == 40:
            col_r = struct.unpack('B', data_stream.read(1))[0]
            col_g = struct.unpack('B', data_stream.read(1))[0]
            col_b = struct.unpack('B', data_stream.read(1))[0]
            col_a = struct.unpack('B', data_stream.read(1))[0]
        else:
            col_r = 0xff
            col_g = 0xff
            col_b = 0xff
            col_a = 0xff
        vrx = Vertex(pos_x, pos_y, pos_z, nrm_x, nrm_y, nrm_z, t_u, t_v, t_w, col_r, col_g, col_b, col_a)
        mesh.append_vertex(vrx)

    # read skinning data if need
    if num_joints > 0:
        for i in range(0, num_vertices):
            joint0 = struct.unpack('B', data_stream.read(1))[0]
            joint1 = struct.unpack('B', data_stream.read(1))[0]
            joint2 = struct.unpack('B', data_stream.read(1))[0]
            joint3 = struct.unpack('B', data_stream.read(1))[0]
            weight0 = struct.unpack('B', data_stream.read(1))[0]
            weight1 = struct.unpack('B', data_stream.read(1))[0]
            weight2 = struct.unpack('B', data_stream.read(1))[0]
            weight3 = struct.unpack('B', data_stream.read(1))[0]

    # read triangles (indices)
    for i in range(0, num_faces):
        index0 = struct.unpack('I', data_stream.read(4))[0]
        index1 = struct.unpack('I', data_stream.read(4))[0]
        index2 = struct.unpack('I', data_stream.read(4))[0]
        tri = Triangle(index0, index1, index2)
        mesh.append_triangle(tri)

    lods = []
    if num_lods > 0:
        for i in range(0, num_lods):
            lod_offset = struct.unpack('I', data_stream.read(4))[0]
            # logger.message(str(i) + " -> " + str(lod_offset))
            lods.append(lod_offset)
    else:
        lods.append(0)
        lods.append(num_faces)

    for i in range(0, num_joints):
        name_offset = struct.unpack('I', data_stream.read(4))[0]
        parent_index = struct.unpack('H', data_stream.read(2))[0]
        lod_index = struct.unpack('H', data_stream.read(2))[0]
        max_skin_radius = struct.unpack('f', data_stream.read(4))[0]
        r00 = struct.unpack('f', data_stream.read(4))[0]
        r01 = struct.unpack('f', data_stream.read(4))[0]
        r02 = struct.unpack('f', data_stream.read(4))[0]
        r10 = struct.unpack('f', data_stream.read(4))[0]
        r11 = struct.unpack('f', data_stream.read(4))[0]
        r12 = struct.unpack('f', data_stream.read(4))[0]
        r20 = struct.unpack('f', data_stream.read(4))[0]
        r21 = struct.unpack('f', data_stream.read(4))[0]
        r22 = struct.unpack('f', data_stream.read(4))[0]
        tx = struct.unpack('f', data_stream.read(4))[0]
        ty = struct.unpack('f', data_stream.read(4))[0]
        tz = struct.unpack('f', data_stream.read(4))[0]

    # ascii name table
    joint_name_table = bytearray(num_joint_name_chars)
    data_stream.readinto(joint_name_table)

    for i in range(0, num_skinning_subsets):
        subset_start_face = struct.unpack('I', data_stream.read(4))[0]
        subset_num_faces = struct.unpack('I', data_stream.read(4))[0]
        subset_start_vertex = struct.unpack('I', data_stream.read(4))[0]
        subset_num_vertices = struct.unpack('I', data_stream.read(4))[0]
        subset_num_joints = struct.unpack('I', data_stream.read(4))[0]
        subset_joint_to_mesh_joint = []
        for j in range(0, 26):
            joint_mapping = struct.unpack('H', data_stream.read(2))[0]
            subset_joint_to_mesh_joint.append(joint_mapping)

    mesh.assign_lod_data(lods)

    # read FACS. data
    if control_to_joint_driver_version != 0 and control_to_joint_driver_size != 0:
        # read facs driver data
        data_stream.read(control_to_joint_driver_size)

    return mesh


def convert_mesh_to_fbx_geometry(mesh: Mesh, lod: int = 0) -> fbx.FbxGeometry:
    # number_of_lods = mesh.get_number_of_lods()
    geo = fbx.FbxGeometry()

    face_from = mesh.lod_data[lod + 0]
    face_to = mesh.lod_data[lod + 1]

    min_index = 999999999
    max_index = -1
    for tri in range(face_from, face_to):
        t = mesh.triangles[tri]
        i0 = t.i0
        i1 = t.i1
        i2 = t.i2
        geo.indices.append(i0)
        geo.indices.append(i1)
        geo.indices.append(i2)
        if i0 < min_index:
            min_index = i0
        if i1 < min_index:
            min_index = i1
        if i2 < min_index:
            min_index = i2
        if i0 > max_index:
            max_index = i0
        if i1 > max_index:
            max_index = i1
        if i2 > max_index:
            max_index = i2

    number_of_vertices = max_index - min_index
    geo.vertices = [fbx.FbxVertex] * (number_of_vertices + 1)

    for i in range(len(geo.indices)):
        index = geo.indices[i]
        vertex = mesh.vertices[index]
        index = index - min_index

        fbx_vertex = fbx.FbxVertex()
        fbx_vertex.x = vertex.p_x
        fbx_vertex.y = vertex.p_y
        fbx_vertex.z = vertex.p_z

        fbx_vertex.nx = vertex.n_x
        fbx_vertex.ny = vertex.n_y
        fbx_vertex.nz = vertex.n_z

        fbx_vertex.u = vertex.u
        fbx_vertex.v = -vertex.v + 1.0

        # noinspection PyTypeChecker
        geo.vertices[index] = fbx_vertex
        geo.indices[i] = index

    return geo


def save_to_obj(file_name: str, mesh: Mesh):
    file_handle = open(file_name, 'w+')

    for v in mesh.vertices:
        line = 'v ' + str(v.p_x) + ' ' + str(v.p_y) + ' ' + str(v.p_z) + '\n'
        file_handle.write(line)

    for v in mesh.vertices:
        line = 'vt ' + str(v.u) + ' ' + str(v.v) + '\n'
        file_handle.write(line)

    for v in mesh.vertices:
        line = 'vn ' + str(v.n_x) + ' ' + str(v.n_y) + ' ' + str(v.n_z) + '\n'
        file_handle.write(line)

    number_of_lods = mesh.get_number_of_lods()
    for lod in range(0, number_of_lods):

        line = 'g m' + 'mesh_lod' + str(lod) + '\n'
        file_handle.write(line)

        face_from = mesh.lod_data[lod + 0]
        face_to = mesh.lod_data[lod + 1]

        for tri in range(face_from, face_to):
            t = mesh.triangles[tri]
            i0 = str(t.i0 + 1)
            i1 = str(t.i1 + 1)
            i2 = str(t.i2 + 1)
            line = 'f ' + \
                   i0 + '/' + i0 + '/' + i0 + ' ' + \
                   i1 + '/' + i1 + '/' + i1 + ' ' + \
                   i2 + '/' + i2 + '/' + i2 + '\n '
            file_handle.write(line)

    file_handle.close()
    return file_name
