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
import math
import io
import sys
import os
import signal
import json
import gzip
import hashlib
import time
import fbx
import rbmesh
import logger
from http.server import BaseHTTPRequestHandler, HTTPServer
import email.utils as email_utils
import urllib.request
import urllib.error


def ensure_path_exist(file_path: str) -> str:
    dir_name = os.path.dirname(file_path)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    return dir_name


def detect_asset_type(content: bytes) -> str:

    if len(content) > 8:
        data_stream = io.BytesIO(content)
        header = data_stream.read(8)
        ktx_header = b'\xab\x4b\x54\x58\x20\x31\x31\xbb'
        if header == ktx_header:
            return 'ktx'

    # ascii mesh
    if len(content) > 12:
        data_stream = io.BytesIO(content)
        header = data_stream.read(12)
        mesh_v1_header = b'version 1.00'
        if header == mesh_v1_header:
            return 'mesh'

    # ascii mesh
    if len(content) > 12:
        data_stream = io.BytesIO(content)
        header = data_stream.read(12)
        mesh_v1_header = b'version 1.01'
        if header == mesh_v1_header:
            return 'mesh'

    # binary mesh
    if len(content) > 12:
        data_stream = io.BytesIO(content)
        header = data_stream.read(12)
        mesh_v1_header = b'version 2.00'
        if header == mesh_v1_header:
            return 'mesh'

    # binary mesh with LODs
    if len(content) > 12:
        data_stream = io.BytesIO(content)
        header = data_stream.read(12)
        mesh_v1_header = b'version 3.00'
        if header == mesh_v1_header:
            return 'mesh'

    # binary mesh with LODs and skinning data
    if len(content) > 12:
        data_stream = io.BytesIO(content)
        header = data_stream.read(12)
        mesh_v4_header = b'version 4.00'
        if header == mesh_v4_header:
            return 'mesh'
        mesh_v41_header = b'version 4.01'
        if header == mesh_v41_header:
            return 'mesh'

    if len(content) > 8:
        data_stream = io.BytesIO(content)
        header = data_stream.read(8)
        png_header = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        if header == png_header:
            return 'png'

    if len(content) > 10:
        data_stream = io.BytesIO(content)
        header = data_stream.read(1)
        _ = data_stream.read(5)
        signature = data_stream.read(4)
        if header == b'\xFF' and signature == b'\x4A\x46\x49\x46':
            return 'jpg'

    if len(content) > 32:
        data_stream = io.BytesIO(content)
        header = data_stream.read(3)
        if header == b'\x44\x44\x53':
            return 'dds'
    return 'raw'


def fetch_local_asset(file_path: str):

    with open(file_path, 'rb') as bin_file:
        data = bin_file.read()
        bin_file.close()

    h256 = hashlib.sha256()
    h256.update(data)

    return {"hash": h256.hexdigest(),
            "cdn_url": file_path,
            "ts": int(0),
            "code": 200,
            "fetched_bytes": len(data),
            "payload_bytes": len(data),
            "payload": data}, None


def fetch_asset(url: str) -> dict or None:
    if not url:
        return None, "Invalid URL"

    if url.startswith('rbxasset://'):
        url = "./built-in/" + url[11:]
        return fetch_local_asset(url)

    asset_fetch_endpoint = 'https://assetdelivery.roblox.com/v1/asset/?id='
    if url.startswith('rbxassetid://'):
        url = asset_fetch_endpoint + url[13:]
    elif url.startswith('https://www.roblox.com/asset/?id='):
        url = asset_fetch_endpoint + url[33:]
    elif url.startswith('http://roblox.com/asset/?id='):
        url = asset_fetch_endpoint + url[28:]
    elif url.startswith('http://www.roblox.com/asset/?id='):
        url = asset_fetch_endpoint + url[32:]

    try:
        request = urllib.request.Request(url)
        request.add_header('Roblox-Place-Id', '0')
        request.add_header('Accept-Encoding', 'gzip')
        request.add_header('User-Agent', 'RobloxStudio/WinInet')

        # noinspection PyUnusedLocal
        fetched_bytes = 0
        response = urllib.request.urlopen(request)
        if response.info().get('Content-Encoding') == 'gzip':
            compressed_data = response.read()
            fetched_bytes = len(compressed_data)
            data = gzip.decompress(compressed_data)
        else:
            data = response.read()
            fetched_bytes = len(data)

        cdn_url = str(response.geturl())

        h256 = hashlib.sha256()
        h256.update(data)

        html_timestamp = response.info().get('Last-Modified')
        timestamp = int(time.mktime(email_utils.parsedate(html_timestamp)))

        return {"hash": h256.hexdigest(),
                "cdn_url": cdn_url,
                "ts": timestamp,
                "code": response.getcode(),
                "fetched_bytes": fetched_bytes,
                "payload_bytes": len(data),
                "payload": data}, None

    except urllib.error.HTTPError as ex:
        logger.warn("Can't fetch asset '" + url + "'")
        logger.warn("Code: " + str(ex.getcode()))
        logger.warn("Exception: '" + str(ex) + "'")
        return None, str(ex)
    except ValueError as ex:
        logger.warn("ValueError. Can't fetch asset " + url)
        logger.warn("Exception: '" + str(ex) + "'")
        return None, str(ex)
    except urllib.error.URLError as ex:
        logger.warn("URLError. Can't fetch asset " + url)
        logger.warn("Exception: '" + str(ex) + "'")
        return None, str(ex)


def resolve_id_to_reference(object_id: int, id_to_object: dict):
    if object_id == -1:
        return None
    else:
        return id_to_object.get(object_id, None)


class SceneDescription:
    def __init__(self):
        self.textures_folder = ""
        self.attachments_layer_id = 0
        self.bones_layer_id = 0
        self.geos_layer_id = 0
        self.accs_layer_id = 0
        self.attachments_material_id = 0


class Connection:
    def __init__(self, is_active, part0, part1):
        self.active = is_active
        self.part0 = part0
        self.part1 = part1


class CFrame:
    def __init__(self):
        self.tx = 0
        self.ty = 0
        self.tz = 0
        self.r00 = 1
        self.r01 = 0
        self.r02 = 0
        self.r10 = 0
        self.r11 = 1
        self.r12 = 0
        self.r20 = 0
        self.r21 = 0
        self.r22 = 1


def cframe_rotation_x(rad: float) -> CFrame:
    cos = math.cos(rad)
    sin = math.sin(rad)
    res = CFrame()
    res.r11 = cos
    res.r12 = -sin
    res.r21 = sin
    res.r22 = cos
    return res


def cframe_translation(x: float, y: float, z: float) -> CFrame:
    res = CFrame()
    res.tx = x
    res.ty = y
    res.tz = z
    return res


def cframe_rotation_y(rad: float) -> CFrame:
    cos = math.cos(rad)
    sin = math.sin(rad)
    res = CFrame()
    res.r00 = cos
    res.r02 = sin
    res.r20 = -sin
    res.r22 = cos
    return res


def cframe_rotation_z(rad: float) -> CFrame:
    cos = math.cos(rad)
    sin = math.sin(rad)
    res = CFrame()
    res.r00 = cos
    res.r01 = -sin
    res.r10 = sin
    res.r11 = cos
    return res


def cframe_roblox_to_maya(cframe: CFrame) -> CFrame:
    res = CFrame()
    res.r00 = cframe.r00
    res.r01 = cframe.r01
    res.r02 = cframe.r02
    res.r10 = cframe.r10
    res.r11 = cframe.r11
    res.r12 = cframe.r12
    res.r20 = cframe.r20
    res.r21 = cframe.r21
    res.r22 = cframe.r22
    res.tx = -cframe.tx
    res.ty = cframe.ty
    res.tz = -cframe.tz
    return res


def cframe_inverse(cframe: CFrame) -> CFrame:
    res = CFrame()

    # transposition
    res.r00 = cframe.r00
    res.r01 = cframe.r10
    res.r02 = cframe.r20

    res.r10 = cframe.r01
    res.r11 = cframe.r11
    res.r12 = cframe.r21

    res.r20 = cframe.r02
    res.r21 = cframe.r12
    res.r22 = cframe.r22

    res.tx = -(res.r00 * cframe.tx + res.r01 * cframe.ty + res.r02 * cframe.tz)
    res.ty = -(res.r10 * cframe.tx + res.r11 * cframe.ty + res.r12 * cframe.tz)
    res.tz = -(res.r20 * cframe.tx + res.r21 * cframe.ty + res.r22 * cframe.tz)

    return res


def cframe_multiply(a: CFrame, b: CFrame) -> CFrame:

    # 3x3 matrix multiplication
    res = CFrame()
    res.r00 = a.r00 * b.r00 + a.r01 * b.r10 + a.r02 * b.r20
    res.r01 = a.r00 * b.r01 + a.r01 * b.r11 + a.r02 * b.r21
    res.r02 = a.r00 * b.r02 + a.r01 * b.r12 + a.r02 * b.r22

    res.r10 = a.r10 * b.r00 + a.r11 * b.r10 + a.r12 * b.r20
    res.r11 = a.r10 * b.r01 + a.r11 * b.r11 + a.r12 * b.r21
    res.r12 = a.r10 * b.r02 + a.r11 * b.r12 + a.r12 * b.r22

    res.r20 = a.r20 * b.r00 + a.r21 * b.r10 + a.r22 * b.r20
    res.r21 = a.r20 * b.r01 + a.r21 * b.r11 + a.r22 * b.r21
    res.r22 = a.r20 * b.r02 + a.r21 * b.r12 + a.r22 * b.r22

    res.tx = a.r00 * b.tx + a.r01 * b.ty + a.r02 * b.tz + a.tx
    res.ty = a.r10 * b.tx + a.r11 * b.ty + a.r12 * b.tz + a.ty
    res.tz = a.r20 * b.tx + a.r21 * b.ty + a.r22 * b.tz + a.tz

    return res


def cframe_transform_pos(cframe: CFrame, x: float, y: float, z: float):
    rx = cframe.r00 * x + cframe.r01 * y + cframe.r02 * z + cframe.tx
    ry = cframe.r10 * x + cframe.r11 * y + cframe.r12 * z + cframe.ty
    rz = cframe.r20 * x + cframe.r21 * y + cframe.r22 * z + cframe.tz
    return rx, ry, rz


def cframe_transform_vec(cframe: CFrame, x: float, y: float, z: float):
    rx = cframe.r00 * x + cframe.r01 * y + cframe.r02 * z
    ry = cframe.r10 * x + cframe.r11 * y + cframe.r12 * z
    rz = cframe.r20 * x + cframe.r21 * y + cframe.r22 * z
    return rx, ry, rz


class Instance:
    def __init__(self):
        self.name = ""
        self.parent = None
        self.children = list()

    def resolve(self, id_to_object: dict):
        self.parent = resolve_id_to_reference(self.parent, id_to_object)
        return


class Part(Instance):
    def __init__(self):
        super().__init__()
        self.sx = 1
        self.sy = 1
        self.sz = 1
        self.cframe = CFrame()

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        return


class MeshPart(Instance):
    def __init__(self):
        super().__init__()
        self.mesh_id = ""
        self.mesh_type = ""
        self.texture_id = ""
        self.cframe = CFrame()
        self.texture_blob = None
        self.mesh_blob = None
        self.offset_x = 0
        self.offset_y = 0
        self.offset_z = 0
        self.scale_x = 1
        self.scale_y = 1
        self.scale_z = 1
        self.size_x = 1
        self.size_y = 1
        self.size_z = 1

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        return


class Model(Instance):
    def __init__(self):
        super().__init__()
        self.primary_part = None

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        self.primary_part = resolve_id_to_reference(self.primary_part, id_to_object)
        return


class Bone(Instance):
    def __init__(self):
        super().__init__()
        self.cframe = CFrame()
        self.m6d = None
        self.cframe_local = None

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        return


class Attachment(Instance):
    def __init__(self):
        super().__init__()
        self.cframe = CFrame()
        self.geo = None

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        return


class Accessory(Instance):
    def __init__(self):
        super().__init__()
        self.attach_point = CFrame()


class Motor6D(Instance):
    def __init__(self):
        super().__init__()
        self.transform = CFrame()
        self.c0 = CFrame()
        self.c1 = CFrame()
        self.part0 = None
        self.part1 = None

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        self.part0 = resolve_id_to_reference(self.part0, id_to_object)
        self.part1 = resolve_id_to_reference(self.part1, id_to_object)
        return


class Weld(Instance):
    def __init__(self):
        super().__init__()
        self.part0 = None
        self.part1 = None

    def resolve(self, id_to_object: dict):
        super().resolve(id_to_object)
        self.part0 = resolve_id_to_reference(self.part0, id_to_object)
        self.part1 = resolve_id_to_reference(self.part1, id_to_object)
        return


def get_cframe(json_cframe) -> CFrame:
    res = CFrame()
    res.tx = json_cframe.get('tx', 0)
    res.ty = json_cframe.get('ty', 0)
    res.tz = json_cframe.get('tz', 0)
    res.r00 = json_cframe.get('r00', 1)
    res.r01 = json_cframe.get('r01', 0)
    res.r02 = json_cframe.get('r02', 0)
    res.r10 = json_cframe.get('r10', 0)
    res.r11 = json_cframe.get('r11', 1)
    res.r12 = json_cframe.get('r12', 0)
    res.r20 = json_cframe.get('r20', 0)
    res.r21 = json_cframe.get('r21', 0)
    res.r22 = json_cframe.get('r22', 1)
    return res


def parse_model_desc(model_desc) -> Instance or None:

    objects = list()
    id_to_object = dict()

    # 1st pass - parse desc and instantiate objects
    for key, dm_object in model_desc.items():
        obj = None
        obj_class = dm_object.get('Class', None)
        assert obj_class is not None
        if obj_class == "Model":
            obj = Model()
            obj.primary_part = dm_object.get('PrimaryPart', -1)
        elif obj_class == "Part":
            obj = Part()
            obj.cframe = get_cframe(dm_object.get('CFrame', CFrame()))
            obj.sx = dm_object.get('SizeX', 1)
            obj.sy = dm_object.get('SizeY', 1)
            obj.sz = dm_object.get('SizeZ', 1)
        elif obj_class == "MeshPart":
            obj = MeshPart()
            obj.mesh_id = dm_object.get('MeshId', '')
            obj.texture_id = dm_object.get('TextureId', '')
            obj.mesh_type = dm_object.get('MeshType', 'Unsupported')
            obj.cframe = get_cframe(dm_object.get('CFrame', CFrame()))

            obj.offset_x = dm_object.get('OffsetX', 1)
            obj.offset_y = dm_object.get('OffsetY', 1)
            obj.offset_z = dm_object.get('OffsetZ', 1)

            obj.scale_x = dm_object.get('ScaleX', 1)
            obj.scale_y = dm_object.get('ScaleY', 1)
            obj.scale_z = dm_object.get('ScaleZ', 1)

            obj.size_x = dm_object.get('SizeX', 1)
            obj.size_y = dm_object.get('SizeY', 1)
            obj.size_z = dm_object.get('SizeZ', 1)
        elif obj_class == "Bone":
            obj = Bone()
            obj.cframe = get_cframe(dm_object.get('CFrame', CFrame()))
        elif obj_class == "Attachment":
            obj = Attachment()
            obj.cframe = get_cframe(dm_object.get('CFrame', CFrame()))
        elif obj_class == "WeldConstraint":
            obj = Weld()
            obj.part0 = dm_object.get('Part0', -1)
            obj.part1 = dm_object.get('Part1', -1)
        elif obj_class == "Motor6D":
            obj = Motor6D()
            obj.part0 = dm_object.get('Part0', -1)
            obj.part1 = dm_object.get('Part1', -1)
            obj.c0 = get_cframe(dm_object.get('C0', CFrame()))
            obj.c1 = get_cframe(dm_object.get('C1', CFrame()))
            obj.transform = get_cframe(dm_object.get('Transform', CFrame()))
        elif obj_class == "Accessory":
            obj = Accessory()
            obj.attach_point = get_cframe(dm_object.get('AttachPoint', CFrame()))
        else:
            logger.fatal("Unknown object type: " + str(obj_class))

        assert obj is not None

        obj.name = dm_object.get('Name', None)
        obj.parent = dm_object.get('Parent', None)

        assert obj.name is not None
        assert obj.parent is not None

        id_to_object[key] = obj
        objects.append(obj)

    # 2nd pass - resolve numeric IDs to real references (and build hierarchy)
    root = None
    for obj in objects:
        obj.resolve(id_to_object)
        if obj.parent is None:
            # multi-root objects not supported
            assert root is None
            root = obj
        else:
            obj.parent.children.append(obj)

    # 3rd pass - fetch actual data from CDN
    data_cache = dict()
    for obj in objects:
        if isinstance(obj, MeshPart):
            obj.mesh_blob = data_cache.get(obj.mesh_id, None)
            if obj.mesh_blob is None:
                logger.message("Fetch mesh: " + obj.mesh_id)
                obj.mesh_blob, err = fetch_asset(obj.mesh_id)
                data_cache[obj.mesh_id] = obj.mesh_blob
            else:
                logger.message("    Cached mesh: " + obj.mesh_id)

            obj.texture_blob = data_cache.get(obj.texture_id, None)
            if obj.texture_blob is None:
                logger.message("    Fetch texture: " + obj.texture_id)
                obj.texture_blob, err = fetch_asset(obj.texture_id)
                data_cache[obj.texture_id] = obj.texture_blob
            else:
                logger.message("    Cached texture: " + obj.texture_id)

    return root


def is_close(x, y, r_tol=1.e-5, a_tol=1.e-8):
    return abs(x-y) <= a_tol + r_tol * abs(y)


def get_bone_name_from_m6d(node: Motor6D):
    return node.part1.name


def get_fbx_transform(cframe: CFrame) -> fbx.FbxTransform:
    xform = fbx.FbxTransform()
    xform.px = cframe.tx
    xform.py = cframe.ty
    xform.pz = cframe.tz

    # Computing Euler angles from a rotation matrix
    # https://www.gregslabaugh.net/publications/euler.pdf
    # R = Rz(phi) * Ry(theta) * Rx(psi)
    phi = 0.0
    if is_close(cframe.r20, -1.0):
        theta = math.pi / 2.0
        psi = math.atan2(cframe.r01, cframe.r02)
    elif is_close(cframe.r20, 1.0):
        theta = -math.pi / 2.0
        psi = math.atan2(-cframe.r01, -cframe.r02)
    else:
        theta = -math.asin(cframe.r20)
        cos_theta = math.cos(theta)
        psi = math.atan2(cframe.r21 / cos_theta, cframe.r22 / cos_theta)
        phi = math.atan2(cframe.r10 / cos_theta, cframe.r00 / cos_theta)

    xform.rx = math.degrees(psi)
    xform.ry = math.degrees(theta)
    xform.rz = math.degrees(phi)

    xform.sx = 1.0
    xform.sy = 1.0
    xform.sz = 1.0
    return xform


def load_mesh(file_name: str) -> rbmesh.Mesh or None:
    mesh_handle = open(file_name, 'rb')
    mesh_payload = mesh_handle.read()
    mesh_handle.close()
    mesh = rbmesh.parse_mesh(mesh_payload)
    return mesh


def load_mesh_as_fbx_geo(file_name: str, cframe: CFrame):
    mesh = load_mesh(file_name)
    mesh_transform_vertices(mesh, cframe)
    geo = rbmesh.convert_mesh_to_fbx_geometry(mesh, 0)
    return geo


def get_texture_name(url: str):
    texture_name = "url_resolve_error"

    if url.startswith('rbxassetid://'):
        texture_name = url[13:]
    elif url.startswith('https://www.roblox.com/asset/?id='):
        texture_name = url[33:]
    elif url.startswith('http://www.roblox.com/asset/?id='):
        texture_name = url[32:]
    elif url.startswith('http://roblox.com/asset/?id='):
        texture_name = url[28:]

    texture_name = texture_name.replace(" ", "")
    texture_name = texture_name.replace("/", "")
    texture_name = texture_name.replace("\\", "")
    texture_name = texture_name.replace("?", "")
    texture_name = texture_name.replace("%", "")
    texture_name = texture_name.replace("*", "")
    texture_name = texture_name.replace(":", "")
    texture_name = texture_name.replace("|", "")
    texture_name = texture_name.replace('"', "")
    texture_name = texture_name.replace('<', "")
    texture_name = texture_name.replace('>', "")
    texture_name = texture_name.replace('.', "")
    texture_name = texture_name.replace('@', "")
    return texture_name


def append_to_fbx(doc, node, fbx_parent_id: int, desc: SceneDescription):
    # noinspection PyUnusedLocal
    fbx_id = 0
    if isinstance(node, MeshPart):
        logger.message("FBX Mesh: " + node.name)
        logger.message("    geo: " + node.mesh_id)
        logger.message("    img: " + node.texture_id)

        xform = get_fbx_transform(node.cframe)

        mesh = None
        if node.mesh_blob is None:
            if node.mesh_type == "Head":
                mesh = load_mesh("./built-in/sm_head.mesh")
                scale_xz = min(node.scale_x, node.scale_z)
                node.scale_x = scale_xz
                node.scale_z = scale_xz
                node.scale_x = node.scale_x / 1.25
                node.scale_y = node.scale_y / 1.25
                node.scale_z = node.scale_z / 1.25
            elif node.mesh_type == "Sphere":
                mesh = load_mesh("./built-in/sm_sphere.mesh")
                node.scale_x = node.scale_x / 1.45
                node.scale_y = node.scale_y / 1.45
                node.scale_z = node.scale_z / 1.45
        else:
            mesh_payload = node.mesh_blob["payload"]
            mesh = rbmesh.parse_mesh(mesh_payload)

        if mesh is None:
            fbx_id = doc.create_locator(node.name, xform, fbx_parent_id)
        else:
            mat_id, mat_name = doc.create_material(node.name + "Mat", fbx.FbxColor4(1, 1, 1, 1))

            texture_file_name = "empty.png"
            if node.texture_blob is not None:
                texture_payload = node.texture_blob["payload"]

                texture_hash = hashlib.sha256(texture_payload).hexdigest()

                texture_ext = detect_asset_type(texture_payload)
                # texture_name = get_texture_name(node.texture_id)
                texture_name = str(texture_hash)
                texture_file_name = texture_name + "." + texture_ext

                full_texture_file_name = desc.textures_folder + texture_file_name
                ensure_path_exist(full_texture_file_name)
                dest_file = open(full_texture_file_name, 'wb')
                dest_file.write(texture_payload)
                dest_file.close()

            doc.create_texture(node.name + "Tex", texture_file_name, mat_id)
            mesh_transform_vertices(mesh, cframe_rotation_y(3.14159),
                                    node.offset_x, node.offset_y, node.offset_z,
                                    node.scale_x, node.scale_y, node.scale_z)

            geo = rbmesh.convert_mesh_to_fbx_geometry(mesh, 0)
            fbx_id = doc.create_mesh(node.name, xform, geo, mat_id, fbx_parent_id)

            doc.connect_objects(fbx_id, desc.geos_layer_id)
    elif isinstance(node, Bone):
        logger.message("FBX Bone: " + node.name)
        xform = get_fbx_transform(node.cframe)
        if node.cframe_local is not None:
            xform = get_fbx_transform(node.cframe_local)
        fbx_id = doc.create_bone(node.name, xform, fbx_parent_id)

        doc.connect_objects(fbx_id, desc.bones_layer_id)
    elif isinstance(node, Attachment):
        logger.message("FBX Attachment: " + node.name)
        xform = get_fbx_transform(node.cframe)
        if node.geo is None:
            fbx_id = doc.create_locator(node.name, xform, fbx_parent_id)
        else:
            fbx_id = doc.create_mesh(node.name, xform, node.geo, desc.attachments_material_id, fbx_parent_id)

        doc.connect_objects(fbx_id, desc.attachments_layer_id)
    else:
        logger.message("FBX Group: " + node.name)
        fbx_id = doc.create_group(node.name, fbx_parent_id)

    for child in node.children:
        append_to_fbx(doc, child, fbx_id, desc)

    return


def _get_linearized_tree_recursive(res: list, node: Instance):
    res.append(node)
    for child in node.children:
        _get_linearized_tree_recursive(res, child)


def get_linearized_tree(root: Instance) -> list:
    res = list()
    res.append(root)

    for child in root.children:
        _get_linearized_tree_recursive(res, child)

    return res


def mesh_transform_vertices(mesh: rbmesh.Mesh, cframe: CFrame,
                            ox: float = 0, oy: float = 0, oz: float = 0,
                            sx: float = 1, sy: float = 1, sz: float = 1):

    for vertex in mesh.vertices:
        x = (vertex.p_x + ox) * sx
        y = (vertex.p_y + oy) * sy
        z = (vertex.p_z + oz) * sz
        vertex.p_x, vertex.p_y, vertex.p_z = cframe_transform_pos(cframe, x, y, z)
        nx = vertex.n_x
        ny = vertex.n_y
        nz = vertex.n_z
        vertex.n_x, vertex.n_y, vertex.n_z = cframe_transform_vec(cframe, nx, ny, nz)

    return


def export_roblox_model(model_desc) -> str:
    root = parse_model_desc(model_desc)
    # logger.message(str(root))

    file_folder = "./Avatars/" + root.name + "/"
    file_name = file_folder + root.name + ".fbx"

    rot_y_180 = cframe_rotation_y(3.14159)
    spike_pivot = cframe_translation(0, 0.5, 0)

    logger.message("Create FBX...")
    doc = fbx.FbxDocument(file_name)
    sphere_geo = load_mesh_as_fbx_geo("./built-in/sphere.mesh", rot_y_180)
    spike_geo = load_mesh_as_fbx_geo("./built-in/spike.mesh", cframe_multiply(rot_y_180, spike_pivot))

    scene_desc = SceneDescription()
    scene_desc.textures_folder = file_folder
    scene_desc.attachments_material_id, _ = doc.create_material("AttachmentMat", fbx.FbxColor4(1, 0.8, 0.8, 1))
    scene_desc.attachments_layer_id = doc.create_layer("Attachments", fbx.FbxColor4(1, 0, 0))
    scene_desc.bones_layer_id = doc.create_layer("Bones", fbx.FbxColor4(0, 0, 1))
    scene_desc.geos_layer_id = doc.create_layer("Geos", fbx.FbxColor4(0, 1, 0))
    scene_desc.accs_layer_id = doc.create_layer("Accs", fbx.FbxColor4(1, 1, 0))

    root_primary_part = None
    scene_center_cframe = CFrame()
    if root.primary_part is not None:
        root_primary_part = root.primary_part
        scene_center_cframe = root.primary_part.cframe

    assert root_primary_part is not None

    # Accessories handler
    accessories = list()
    for child in root.children:
        if isinstance(child, Accessory):
            child.parent = None
            accessories.append(child)
            logger.message("Accessory: " + child.name)
    for accessory in accessories:
        root.children.remove(accessory)

    # convert part based rig (Motor6Ds) to bone based
    nodes = get_linearized_tree(root)

    # Step 0. Cover a special case, in R15 case everything should be centered around LowerTorso
    for node in nodes:
        if isinstance(node, Motor6D) and node.name == "Root":
            scene_center_cframe = cframe_multiply(node.part0.cframe, node.c0)
            break

    scene_center_cframe_inv = cframe_inverse(scene_center_cframe)

    # Step 1. Center the scene
    logger.message("1. Center scene")
    for node in nodes:
        if isinstance(node, Part) or isinstance(node, MeshPart) or isinstance(node, Bone):
            node.cframe = cframe_multiply(scene_center_cframe_inv, node.cframe)

    # Step 2. Generate bones from motor6Ds
    logger.message("2. Generate bones")
    bones = list()

    humanoid_root_bone = Bone()
    humanoid_root_bone.name = "HumanoidRootNode"
    humanoid_root_bone.parent = None
    humanoid_root_bone.cframe = CFrame()
    humanoid_root_bone.cframe_local = CFrame()
    humanoid_root_bone.m6d = None
    bones.append(humanoid_root_bone)

    for node in nodes:
        # skip HumanoidRootPart
        if node == root_primary_part:
            continue

        if isinstance(node, Motor6D):
            bone = Bone()
            bone.name = get_bone_name_from_m6d(node)
            bone.parent = None
            bone.m6d = node
            #
            # these two matrices below are equal
            # get_fbx_transform(cframe_multiply(node.part1.cframe, node.c1))
            # get_fbx_transform(cframe_multiply(node.part0.cframe, node.c0))
            bone.cframe = cframe_roblox_to_maya(cframe_multiply(node.part0.cframe, node.c0))
            bones.append(bone)

    # Step 3. Rename geos
    logger.message("3. Rename geos")
    for node in nodes:
        if isinstance(node, Part) or isinstance(node, MeshPart):
            node.name = node.name + "_Geo"

    # Step 4. Reconstruct hierarchy
    logger.message("4. Build hierarchy")
    already_connected_parts = dict()
    already_connected_parts[root_primary_part] = humanoid_root_bone

    bones_to_process = list()
    while True:
        bones_to_process.clear()
        for bone in bones:
            # ignore already processed bones
            if bone.m6d is None:
                continue

            parent_bone0 = already_connected_parts.get(bone.m6d.part0, None)
            parent_bone1 = already_connected_parts.get(bone.m6d.part1, None)

            child_part = None
            parent_bone = None
            if parent_bone0 is not None:
                assert parent_bone1 is None
                parent_bone = parent_bone0
                child_part = bone.m6d.part1

            if parent_bone1 is not None:
                assert parent_bone0 is None
                parent_bone = parent_bone1
                child_part = bone.m6d.part0

            if parent_bone is None:
                continue

            bones_to_process.append((parent_bone, child_part, bone))

        for parent_bone, child_part, child_bone in bones_to_process:
            logger.message(parent_bone.name + " -> " + child_bone.name + "/" + child_part.name)
            child_bone.m6d = None
            child_bone.parent = parent_bone
            parent_bone.children.append(child_bone)
            child_bone.cframe_local = cframe_multiply(cframe_inverse(parent_bone.cframe), child_bone.cframe)
            already_connected_parts[child_part] = child_bone

        number_of_bones_to_process = 0
        for bone in bones:
            if bone.m6d is not None:
                number_of_bones_to_process += 1

        if number_of_bones_to_process == 0:
            break

    # Step 6. Rotate by 180 degree and add root bones to the FBX scene
    for node in nodes:
        if isinstance(node, Attachment):
            # from Roblox local space to Maya world space
            node.cframe = cframe_roblox_to_maya(cframe_multiply(node.parent.cframe, node.cframe))

    for node in nodes:
        if isinstance(node, Part) or isinstance(node, MeshPart):
            # from Roblox world space to Maya world space
            node.cframe = cframe_roblox_to_maya(node.cframe)

    # Step 7. Attach mesh part to corresponding bones
    # a) built attachments list
    geom_to_attachments = dict()
    for node in nodes:
        if isinstance(node, Attachment) and not node.name.endswith("RigAttachment"):
            if node.name.endswith("Attachment"):
                node.name = node.name[:-10] + "_Att"

            parent_geo_name = node.parent.name
            geo_attachments = geom_to_attachments.get(parent_geo_name, None)
            if not geo_attachments:
                geo_attachments = list()
                geom_to_attachments[parent_geo_name] = geo_attachments

            geo_attachments.append(node)

    # b) destroy existing hierarchy (unlink)
    for node in nodes:
        node.children.clear()
        node.parent = None

    # c) add geo/attachments to corresponding bones
    for bone in bones:
        part_name = bone.name + "_Geo"
        for node in nodes:
            if node.name == part_name and (isinstance(node, Part) or isinstance(node, MeshPart)):
                node.cframe = cframe_multiply(cframe_inverse(bone.cframe), node.cframe)
                node.parent = bone
                bone.children.append(node)

        geo_attachments = geom_to_attachments.get(part_name, None)
        if geo_attachments:
            for attachment in geo_attachments:

                if attachment.name == "LeftGrip_Att" or attachment.name == "RightGrip_Att":
                    #
                    # https://developer.roblox.com/en-us/articles/using-avatar-importer
                    #
                    # The LeftGrip_Att and RightGrip_Att attachments have a 90 deg rotation on the X axis.
                    # In short, their rotation should be (90, 0, 0).
                    #
                    attachment.cframe = cframe_multiply(attachment.cframe, cframe_rotation_x(3.14159))
                    attachment.geo = spike_geo
                else:
                    attachment.geo = sphere_geo

                attachment.cframe = cframe_multiply(cframe_inverse(bone.cframe), attachment.cframe)
                attachment.parent = bone
                bone.children.append(attachment)

    root_bone_id = doc.create_bone("Root", fbx.FbxTransform())
    doc.connect_objects(root_bone_id, scene_desc.bones_layer_id)

    root_att_id = doc.create_mesh("Root_Att", fbx.FbxTransform(),
                                  sphere_geo, scene_desc.attachments_material_id, root_bone_id)
    doc.connect_objects(root_att_id, scene_desc.attachments_layer_id)

    append_to_fbx(doc, humanoid_root_bone, root_bone_id, scene_desc)

    if len(accessories) > 0:
        accessories_id = doc.create_group("Accessories")
        doc.connect_objects(accessories_id, scene_desc.accs_layer_id)
        for accessory in accessories:
            accessory_name = accessory.name
            if accessory_name.endswith("Accessory"):
                accessory_name = accessory_name[:-9] + "_Acc"

            accessory_nodes = get_linearized_tree(accessory)

            # move attachments to world space
            for accessory_node in accessory_nodes:
                if isinstance(accessory_node, Attachment) and accessory_node.parent is not None:
                    accessory_node.cframe = cframe_multiply(accessory_node.parent.cframe, accessory_node.cframe)

            # destroy existing hierarchy
            for accessory_node in accessory_nodes:
                accessory_node.children.clear()
                accessory_node.parent = None

            root_accessory_id = doc.create_group(accessory_name, accessories_id)

            for accessory_node in accessory_nodes:
                if isinstance(accessory_node, MeshPart):
                    # Center accessory
                    accessory_node.cframe = cframe_multiply(scene_center_cframe_inv, accessory_node.cframe)
                    # from Roblox world space to Maya world space
                    accessory_node.cframe = cframe_roblox_to_maya(accessory_node.cframe)
                    append_to_fbx(doc, accessory_node, root_accessory_id, scene_desc)

                if isinstance(accessory_node, Attachment):
                    accessory_node.geo = sphere_geo

                    # Center accessory
                    accessory_node.cframe = cframe_multiply(scene_center_cframe_inv, accessory_node.cframe)
                    # from Roblox world space to Maya world space
                    accessory_node.cframe = cframe_roblox_to_maya(accessory_node.cframe)

                    append_to_fbx(doc, accessory_node, root_accessory_id, scene_desc)

    text = doc.finalize()

    logger.message("Save FBX...")
    ensure_path_exist(file_name)
    file_handle = open(file_name, 'w+')
    file_handle.write(text)
    file_handle.close()

    return "Saved file:" + file_name


class ForgeHTTPArtServerRequestHandler(BaseHTTPRequestHandler):

    # noinspection PyPep8Naming
    def do_POST(self):

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')

        model_description = json.loads(body)
        # result = fetch_roblox_model_to_disk(model_description)
        result = export_roblox_model(model_description)

        self.send_response(200)

        # Send headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Write content as utf-8 data
        self.wfile.write(bytes(result, "utf8"))
        return

    # noinspection PyPep8Naming
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = "{"

        # add heads
        heads_file = open('./heads.txt', 'r')
        if heads_file:
            response += '"heads": ['
            lines = heads_file.readlines()
            need_comma = False
            for line in lines:
                ln = line.rstrip()
                if not ln.isdigit():
                    continue
                if need_comma:
                    response += ", "
                response += ln
                need_comma = True
            response += '], '
        else:
            logger.warn("Can't open heads.txt")

        # add bundles
        bundles_file = open('./bundles.txt', 'r')
        if bundles_file:
            response += '"bundles": ['
            lines = bundles_file.readlines()
            need_comma = False
            for line in lines:
                ln = line.rstrip()
                if not ln.isdigit():
                    continue
                if need_comma:
                    response += ", "
                response += ln
                need_comma = True
            response += ']'
        else:
            logger.warn("Can't open bundles.txt")

        response += "}"
        self.wfile.write(bytes(response, "utf8"))
        return


def signal_handler(_signal, _frame):
    logger.message('\nAvatar FBX Exporter Server closed by user request.')
    sys.exit(0)


def main():
    if sys.version_info[0] != 3:
        logger.fatal("Python3 required")

    signal.signal(signal.SIGINT, signal_handler)

    server_address = ('127.0.0.1', 49999)

    httpd = HTTPServer(server_address, ForgeHTTPArtServerRequestHandler)
    logger.message('Roblox Avatar FBX Exporter Server "{0}:{1}"'.format(server_address[0], server_address[1]))
    logger.message('by Sergey Makeev\n')
    logger.message('Press Ctrl+C to exit')
    httpd.serve_forever()


main()
