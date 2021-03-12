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
import uuid
import datetime


def normalize_file_path(path):
    path = path.replace('\\', '/')
    # remove double slashes
    while path.find('//') >= 0:
        path = path.replace('//', '/')
    return path


def get_filename_without_ext(path):
    path = normalize_file_path(path)
    prefix_index = path.rfind('/')
    if prefix_index >= 0:
        path = path[prefix_index+1:]

    postfix_index = path.rfind('.')
    if postfix_index >= 0:
        path = path[:postfix_index]

    return path


def fbx_generate_id():
    u = uuid.uuid4()
    uid = u.int
    return str(uid)[:13]


class FbxVertex:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

        self.nx = 0
        self.ny = 0
        self.nz = 0

        self.u = 0
        self.v = 0


class FbxGeometry:
    def __init__(self):
        self.vertices = []
        self.indices = []


class FbxTransform:
    def __init__(self, *args):
        self.px = 0
        self.py = 0
        self.pz = 0

        self.rx = 0
        self.ry = 0
        self.rz = 0

        self.sx = 1
        self.sy = 1
        self.sz = 1

        args_count = len(args)
        if args_count >= 3:
            self.px = args[0]
            self.py = args[1]
            self.pz = args[2]

        if args_count >= 6:
            self.rx = args[3]
            self.ry = args[4]
            self.rz = args[5]

        if args_count == 9:
            self.sx = args[6]
            self.sy = args[7]
            self.sz = args[8]

        return


class FbxColor4:
    def __init__(self, *args):
        self.r = 0
        self.g = 0
        self.b = 0
        self.a = 1

        args_count = len(args)
        if args_count >= 3:
            self.r = args[0]
            self.g = args[1]
            self.b = args[2]

        if args_count == 4:
            self.a = args[3]
        return


class FbxDocument:
    def __init__(self, name: str):
        self.scene_objects = dict()
        self.text_chunks = []
        self.connections = []
        self.named_connections = []
        self._create_header(name)
        self._begin_objects()

    def _get_unique_name(self, name: str):
        current_name = name
        for i in range(0, 5000):
            if current_name not in self.scene_objects:
                # value is not important here
                self.scene_objects[current_name] = name
                return current_name
            current_name = name + str(i)

        # give up and generate ID instead
        current_name = str(uuid.uuid4())
        self.scene_objects[current_name] = name
        return current_name.replace("-", "")

    def _append_line(self, txt: str):
        self.text_chunks.append(txt)
        self.text_chunks.append("\n")

    def _append(self, txt: str):
        self.text_chunks.append(txt)

    def _create_header(self, name: str):
        name = get_filename_without_ext(name)
    
        self._append_line("; FBX 7.3.0 project file")
        self._append_line("; ----------------------------------------------------")
        self._append_line("")

        self._append_line("FBXHeaderExtension:  {")
        self._append_line("\tFBXHeaderVersion: 1003")
        self._append_line("\tFBXVersion: 7300")
    
        d = datetime.datetime.today()
        self._append_line("\tCreationTimeStamp:  {")
        self._append_line("\t\tVersion: 1000")
        self._append_line("\t\tYear: " + str(d.year))
        self._append_line("\t\tMonth: " + str(d.month))
        self._append_line("\t\tDay: " + str(d.day))
        self._append_line("\t\tHour: " + str(d.hour))
        self._append_line("\t\tMinute: " + str(d.minute))
        self._append_line("\t\tSecond: " + str(d.second))
        self._append_line("\t\tMillisecond: " + str(round(d.microsecond / 1000)))
        self._append_line("\t}")
    
        self._append_line("\tCreator: \"The Forge FBX Exporter\"")
        self._append_line("\tSceneInfo: \"SceneInfo::GlobalInfo\", \"UserData\" {")
        self._append_line("\t\tType: \"UserData\"")
        self._append_line("\t\tVersion: 100")
        self._append_line("\t\tMetaData:  {")
        self._append_line("\t\t\tVersion: 100")
        self._append_line("\t\t\tTitle: \"\"")
        self._append_line("\t\t\tSubject: \"\"")
        self._append_line("\t\t\tAuthor: \"\"")
        self._append_line("\t\t\tKeywords: \"\"")
        self._append_line("\t\t\tRevision: \"\"")
        self._append_line("\t\t\tComment: \"\"")
        self._append_line("\t\t}")
        self._append_line("\t\tProperties70:  {")
    
        self._append_line("\t\t\tP: \"DocumentUrl\", \"KString\", \"Url\", \"\", \"" + name + ".fbx\"")
        self._append_line("\t\t\tP: \"SrcDocumentUrl\", \"KString\", \"Url\", \"\", \"" + name + ".fbx\"")
        self._append_line("\t\t\tP: \"Original\", \"Compound\", \"\", \"\"")
        self._append_line("\t\t\tP: \"Original|ApplicationVendor\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"Original|ApplicationName\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"Original|ApplicationVersion\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"Original|DateTime_GMT\", \"DateTime\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"Original|FileName\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"LastSaved\", \"Compound\", \"\", \"\"")
        self._append_line("\t\t\tP: \"LastSaved|ApplicationVendor\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"LastSaved|ApplicationName\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"LastSaved|ApplicationVersion\", \"KString\", \"\", \"\", \"\"")
        self._append_line("\t\t\tP: \"LastSaved|DateTime_GMT\", \"DateTime\", \"\", \"\", \"\"")
        self._append_line("\t\t}")
        self._append_line("\t}")
        self._append_line("}")
    
        self._append_line("GlobalSettings:  {")
        self._append_line("\tVersion: 1000")
        self._append_line("\tProperties70:  {")
        self._append_line("\t\tP: \"UpAxis\", \"int\", \"Integer\", \"\",1")
        self._append_line("\t\tP: \"UpAxisSign\", \"int\", \"Integer\", \"\",1")
        self._append_line("\t\tP: \"FrontAxis\", \"int\", \"Integer\", \"\",2")
        self._append_line("\t\tP: \"FrontAxisSign\", \"int\", \"Integer\", \"\",1")
        self._append_line("\t\tP: \"CoordAxis\", \"int\", \"Integer\", \"\",0")
        self._append_line("\t\tP: \"CoordAxisSign\", \"int\", \"Integer\", \"\",1")
        self._append_line("\t\tP: \"OriginalUpAxis\", \"int\", \"Integer\", \"\",-1")
        self._append_line("\t\tP: \"OriginalUpAxisSign\", \"int\", \"Integer\", \"\",1")
        self._append_line("\t\tP: \"UnitScaleFactor\", \"double\", \"Number\", \"\",1")
        self._append_line("\t\tP: \"OriginalUnitScaleFactor\", \"double\", \"Number\", \"\",100")
        self._append_line("\t\tP: \"AmbientColor\", \"ColorRGB\", \"Color\", \"\",0,0,0")
        self._append_line("\t\tP: \"DefaultCamera\", \"KString\", \"\", \"\", \"Producer Perspective\"")
        self._append_line("\t\tP: \"TimeMode\", \"enum\", \"\", \"\",11")
        self._append_line("\t\tP: \"TimeSpanStart\", \"KTime\", \"Time\", \"\",0")
        self._append_line("\t\tP: \"TimeSpanStop\", \"KTime\", \"Time\", \"\",479181389250")
        self._append_line("\t\tP: \"CustomFrameRate\", \"double\", \"Number\", \"\",-1")
        self._append_line("\t}")
        self._append_line("}")
    
        self._append_line("; Document References")
        self._append_line(";------------------------------------------------------------------")
        self._append_line("")
        self._append_line("References:  {")
        self._append_line("}")
    
        self._append_line("; Object definitions")
        self._append_line(";------------------------------------------------------------------")
        self._append_line("")
        self._append_line("Definitions:  {")
        self._append_line("\tVersion: 100")
        self._append_line("\tCount: 8")
    
        self._append_line("\tObjectType: \"GlobalSettings\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t}")
    
        self._append_line("\tObjectType: \"Model\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t\tPropertyTemplate: \"FbxNode\" {")
        self._append_line("\t\t\tProperties70:  {")
        self._append_line("\t\t\t\tP: \"QuaternionInterpolate\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationOffset\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"RotationPivot\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"ScalingOffset\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"ScalingPivot\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"TranslationActive\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"TranslationMin\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"TranslationMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"TranslationMinX\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"TranslationMinY\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"TranslationMinZ\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"TranslationMaxX\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"TranslationMaxY\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"TranslationMaxZ\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationOrder\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationSpaceForLimitOnly\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationStiffnessX\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationStiffnessY\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationStiffnessZ\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"AxisLen\", \"double\", \"Number\", \"\",10")
        self._append_line("\t\t\t\tP: \"PreRotation\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"PostRotation\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"RotationActive\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationMin\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"RotationMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"RotationMinX\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationMinY\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationMinZ\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationMaxX\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationMaxY\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"RotationMaxZ\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"InheritType\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingActive\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingMin\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"ScalingMax\", \"Vector3D\", \"Vector\", \"\",1,1,1")
        self._append_line("\t\t\t\tP: \"ScalingMinX\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingMinY\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingMinZ\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingMaxX\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingMaxY\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"ScalingMaxZ\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"GeometricTranslation\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"GeometricRotation\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"GeometricScaling\", \"Vector3D\", \"Vector\", \"\",1,1,1")
        self._append_line("\t\t\t\tP: \"MinDampRangeX\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MinDampRangeY\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MinDampRangeZ\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MaxDampRangeX\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MaxDampRangeY\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MaxDampRangeZ\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MinDampStrengthX\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MinDampStrengthY\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MinDampStrengthZ\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MaxDampStrengthX\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MaxDampStrengthY\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"MaxDampStrengthZ\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"PreferedAngleX\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"PreferedAngleY\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"PreferedAngleZ\", \"double\", \"Number\", \"\",0")
        self._append_line("\t\t\t\tP: \"LookAtProperty\", \"object\", \"\", \"\"")
        self._append_line("\t\t\t\tP: \"UpVectorProperty\", \"object\", \"\", \"\"")
        self._append_line("\t\t\t\tP: \"Show\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"NegativePercentShapeSupport\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"DefaultAttributeIndex\", \"int\", \"Integer\", \"\",-1")
        self._append_line("\t\t\t\tP: \"Freeze\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"LODBox\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"Lcl Translation\", \"Lcl Translation\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\t\tP: \"Lcl Rotation\", \"Lcl Rotation\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\t\tP: \"Lcl Scaling\", \"Lcl Scaling\", \"\", \"A\",1,1,1")
        self._append_line("\t\t\t\tP: \"Visibility\", \"Visibility\", \"\", \"A\",1")
        self._append_line("\t\t\t\tP: \"Visibility Inheritance\", \"Visibility Inheritance\", \"\", \"\",1")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")
        self._append_line("\t}")

        self._append_line("\tObjectType: \"CollectionExclusive\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t\tPropertyTemplate: \"FbxDisplayLayer\" {")
        self._append_line("\t\t\tProperties70:  {")
        self._append_line("\t\t\t\tP: \"Color\", \"ColorRGB\", \"Color\", \"\",0.8,0.8,0.8")
        self._append_line("\t\t\t\tP: \"Show\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"Freeze\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"LODBox\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")
        self._append_line("\t}")

        self._append_line("\tObjectType: \"NodeAttribute\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t\tPropertyTemplate: \"FbxNull\" {")
        self._append_line("\t\t\tProperties70:  {")
        self._append_line("\t\t\t\tP: \"Color\", \"ColorRGB\", \"Color\", \"\",0.8,0.8,0.8")
        self._append_line("\t\t\t\tP: \"Size\", \"double\", \"Number\", \"\",100")
        self._append_line("\t\t\t\tP: \"Look\", \"enum\", \"\", \"\",1")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")
        self._append_line("\t}")

        self._append_line("\tObjectType: \"Pose\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t}")

        self._append_line("\tObjectType: \"Deformer\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t}")

        self._append_line("\tObjectType: \"Geometry\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t\tPropertyTemplate: \"FbxMesh\" {")
        self._append_line("\t\t\tProperties70:  {")
        self._append_line("\t\t\t\tP: \"Color\", \"ColorRGB\", \"Color\", \"\",0.8,0.8,0.8")
        self._append_line("\t\t\t\tP: \"BBoxMin\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"BBoxMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"Primary Visibility\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"Casts Shadows\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"Receive Shadows\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")
        self._append_line("\t}")
    
        self._append_line("\tObjectType: \"Material\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t\tPropertyTemplate: \"FbxSurfaceLambert\" {")
        self._append_line("\t\t\tProperties70:  {")
        self._append_line("\t\t\t\tP: \"ShadingModel\", \"KString\", \"\", \"\", \"Lambert\"")
        self._append_line("\t\t\t\tP: \"MultiLayer\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"EmissiveColor\", \"Color\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\t\tP: \"EmissiveFactor\", \"Number\", \"\", \"A\",1")
        self._append_line("\t\t\t\tP: \"AmbientColor\", \"Color\", \"\", \"A\",0.2,0.2,0.2")
        self._append_line("\t\t\t\tP: \"AmbientFactor\", \"Number\", \"\", \"A\",1")
        self._append_line("\t\t\t\tP: \"DiffuseColor\", \"Color\", \"\", \"A\",0.8,0.8,0.8")
        self._append_line("\t\t\t\tP: \"DiffuseFactor\", \"Number\", \"\", \"A\",1")
        self._append_line("\t\t\t\tP: \"Bump\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"NormalMap\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"BumpFactor\", \"double\", \"Number\", \"\",1")
        self._append_line("\t\t\t\tP: \"TransparentColor\", \"Color\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\t\tP: \"TransparencyFactor\", \"Number\", \"\", \"A\",0")
        self._append_line("\t\t\t\tP: \"DisplacementColor\", \"ColorRGB\", \"Color\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"DisplacementFactor\", \"double\", \"Number\", \"\",1")
        self._append_line("\t\t\t\tP: \"VectorDisplacementColor\", \"ColorRGB\", \"Color\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"VectorDisplacementFactor\", \"double\", \"Number\", \"\",1")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")
        self._append_line("\t}")
    
        self._append_line("\tObjectType: \"Texture\" {")
        self._append_line("\t\tCount: 1")
        self._append_line("\t\tPropertyTemplate: \"FbxFileTexture\" {")
        self._append_line("\t\t\tProperties70:  {")
        self._append_line("\t\t\t\tP: \"TextureTypeUse\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"Texture alpha\", \"Number\", \"\", \"A\",1")
        self._append_line("\t\t\t\tP: \"CurrentMappingType\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"WrapModeU\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"WrapModeV\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"UVSwap\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"PremultiplyAlpha\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"Translation\", \"Vector\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\t\tP: \"Rotation\", \"Vector\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\t\tP: \"Scaling\", \"Vector\", \"\", \"A\",1,1,1")
        self._append_line("\t\t\t\tP: \"TextureRotationPivot\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"TextureScalingPivot\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\t\tP: \"CurrentTextureBlendMode\", \"enum\", \"\", \"\",1")
        self._append_line("\t\t\t\tP: \"UVSet\", \"KString\", \"\", \"\", \"default\"")
        self._append_line("\t\t\t\tP: \"UseMaterial\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t\tP: \"UseMipMap\", \"bool\", \"\", \"\",0")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")
        self._append_line("\t}")
    
        self._append_line("}")
        self._append_line("")
        return

    def _begin_objects(self):
        self._append_line("; Object properties;")
        self._append_line(";------------------------------------------------------------------")
        self._append_line("")
        self._append_line("Objects:  {")
        return
    
    def _end_objects(self):
        self._append_line("}")
        return

    def create_layer(self, name: str, color: FbxColor4):
        name = self._get_unique_name(name)
        r = color.r
        g = color.g
        b = color.b
        uid = fbx_generate_id()
        self._append_line("\tCollectionExclusive: " + uid + ", \"DisplayLayer::" + name + "\", \"DisplayLayer\" {")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"Color\", \"ColorRGB\", \"Color\", \"\",{:.3f},{:.3f},{:.3f}".format(r, g, b))
        self._append_line("\t\t}")
        self._append_line("\t}")
        return uid

    def create_group(self, group_name: str, parent_id: int = 0):
        group_name = self._get_unique_name(group_name)
        uid = fbx_generate_id()
        self._append_line("\tModel: " + uid + ", \"Model::" + group_name + "\", \"Null\" {")
        self._append_line("\t\tVersion: 232")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"RotationActive\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"InheritType\", \"enum\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"ScalingMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\tP: \"DefaultAttributeIndex\", \"int\", \"Integer\", \"\",0")
        self._append_line("\t\t}")
        self._append_line("\t\tShading: Y")
        self._append_line("\t\tCulling: \"CullingOff\"")
        self._append_line("\t}")
        self.connections.append((uid, parent_id))
        return uid
    
    def create_locator(self, locator_name: str, t: FbxTransform, parent_id: int = 0):
        locator_name = self._get_unique_name(locator_name)
        attr_uid = fbx_generate_id()
        self._append_line("\tNodeAttribute: " + attr_uid + ", \"NodeAttribute::\", \"Null\" {")
        self._append_line("\t\tTypeFlags: \"Null\"")
        self._append_line("\t}")
    
        uid = fbx_generate_id()
        self._append_line("\tModel: " + uid + ", \"Model::" + locator_name + "\", \"Null\" {")
        self._append_line("\t\tVersion: 232")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"RotationActive\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"InheritType\", \"enum\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"ScalingMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\tP: \"DefaultAttributeIndex\", \"int\", \"Integer\", \"\",0")
        self._append_line(
            "\t\t\tP: \"Lcl Translation\", \"Lcl Translation\", \"\", \"A\",{0},{1},{2}".format(t.px, t.py, t.pz))
        self._append_line(
            "\t\t\tP: \"Lcl Rotation\", \"Lcl Rotation\", \"\", \"A\",{0},{1},{2}".format(t.rx, t.ry, t.rz))
        self._append_line(
            "\t\t\tP: \"Lcl Scaling\", \"Lcl Scaling\", \"\", \"A\",{0},{1},{2}".format(t.sx, t.sy, t.sz))
        self._append_line("\t\t}")
        self._append_line("\t\tShading: Y")
        self._append_line("\t\tCulling: \"CullingOff\"")
        self._append_line("\t}")
        self.connections.append((uid, parent_id))
        self.connections.append((attr_uid, uid))
        return uid

    def create_bone(self, bone_name: str, t: FbxTransform, parent_id: int = 0):
        bone_name = self._get_unique_name(bone_name)
        attr_uid = fbx_generate_id()
        self._append_line("\tNodeAttribute: " + attr_uid + ", \"NodeAttribute::\", \"LimbNode\" {")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"Size\", \"double\", \"Number\", \"\",10.0")
        self._append_line("\t\t}")
        self._append_line("\t\tTypeFlags: \"Skeleton\"")
        self._append_line("\t}")

        uid = fbx_generate_id()
        self._append_line("\tModel: " + uid + ", \"Model::" + bone_name + "\", \"LimbNode\" {")
        self._append_line("\t\tVersion: 232")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"PreRotation\", \"Vector3D\", \"Vector\", \"\",0, 0, 0")
        self._append_line("\t\t\tP: \"RotationActive\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"InheritType\", \"enum\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"ScalingMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\tP: \"DefaultAttributeIndex\", \"int\", \"Integer\", \"\",0")
        self._append_line(
            "\t\t\tP: \"Lcl Translation\", \"Lcl Translation\", \"\", \"A\",{0},{1},{2}".format(t.px, t.py, t.pz))
        self._append_line(
            "\t\t\tP: \"Lcl Rotation\", \"Lcl Rotation\", \"\", \"A\",{0},{1},{2}".format(t.rx, t.ry, t.rz))
        self._append_line(
            "\t\t\tP: \"Lcl Scaling\", \"Lcl Scaling\", \"\", \"A\",{0},{1},{2}".format(t.sx, t.sy, t.sz))
        self._append_line("\t\t}")
        self._append_line("\t\tShading: Y")
        self._append_line("\t\tCulling: \"CullingOff\"")
        self._append_line("\t}")
        self.connections.append((uid, parent_id))
        self.connections.append((attr_uid, uid))
        return uid

    def create_texture(self, texture_name: str, file_name: str, mat_id: int, connection_name: str = "DiffuseColor"):
        texture_name = self._get_unique_name(texture_name)
        uid = fbx_generate_id()
        self._append_line("\tTexture: " + uid + ", \"Texture::" + texture_name + "\", \"\" {")
        self._append_line("\t\tType: \"TextureVideoClip\"")
        self._append_line("\t\tVersion: 202")
        self._append_line("\t\tTextureName: \"Texture::" + texture_name + "\"")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"CurrentTextureBlendMode\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\tP: \"UVSet\", \"KString\", \"\", \"\",\"map1\"")
        self._append_line("\t\t\tP: \"UseMaterial\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t}")
        self._append_line("\t\tMedia: \"Video::" + texture_name + "\"")
        self._append_line("\t\tFileName: \"" + file_name + "\"")
        self._append_line("\t\tRelativeFilename: \"" + file_name + "\"")
        self._append_line("\t\tModelUVTranslation: 0,0")
        self._append_line("\t\tModelUVScaling: 1,1")
        self._append_line("\t\tTexture_Alpha_Source: \"None\"")
        self._append_line("\t\tCropping: 0,0,0,0")
        self._append_line("\t}")
        self.named_connections.append((uid, mat_id, connection_name))
        return uid

    def create_material(self, material_name: str, color: FbxColor4):
        material_name = self._get_unique_name(material_name)
        r = color.r
        g = color.g
        b = color.b
        a = color.a
        t = 1.0 - a
        uid = fbx_generate_id()
        self._append_line("\tMaterial: " + uid + ", \"Material::" + material_name + "\", \"\" {")
        self._append_line("\t\tVersion: 102")
        self._append_line("\t\tShadingModel: \"lambert\"")
        self._append_line("\t\tMultiLayer: 0")
        self._append_line("\t\tProperties70:  {")
        self._append_line("\t\t\tP: \"AmbientColor\", \"Color\", \"\", \"A\",0,0,0")
        self._append_line("\t\t\tP: \"DiffuseColor\", \"Color\", \"\", \"A\",{:.3f},{:.3f},{:.3f}".format(r, g, b))
        self._append_line("\t\t\tP: \"DiffuseFactor\", \"Number\", \"\", \"A\",1.0")
        self._append_line("\t\t\tP: \"TransparentColor\", \"Color\", \"\", \"A\",{:.3f},{:.3f},{:.3f}".format(t, t, t))
        self._append_line("\t\t\tP: \"TransparencyFactor\", \"Number\", \"\", \"A\",1")
        self._append_line("\t\t\tP: \"Emissive\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\tP: \"Ambient\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\tP: \"Diffuse\", \"Vector3D\", \"Vector\", \"\",{:.2f},{:.2f},{:.2f}".format(r, g, b))
        self._append_line("\t\t\tP: \"Opacity\", \"double\", \"Number\", \"\",{:.3f}".format(a))
        self._append_line("\t\t}")
        self._append_line("\t}")
        return uid, material_name

    # Connects object to layer (but in theory can connect anything)
    def connect_objects(self, object_id: int, layer_id: int):
        if object_id == 0 or layer_id == 0:
            return
        self.connections.append((object_id, layer_id))

    def create_mesh(self, mesh_name: str, t: FbxTransform, geo: FbxGeometry, material_id: int = 0, parent_id: int = 0):
        mesh_name = self._get_unique_name(mesh_name)
        geom_id = fbx_generate_id()
        self._append_line("\tGeometry: " + geom_id + ", \"Geometry::\", \"Mesh\" {")

        vertices_count = len(geo.vertices)
        indices_count = len(geo.indices)

        # vertices
        self._append_line("\t\tVertices: *" + str(vertices_count * 3) + " {")
        self._append("\t\t\ta: ")
        for i, vertex in enumerate(geo.vertices):
            if i > 0:
                self._append(",")
            self._append("{0},{1},{2}".format(vertex.x, vertex.y, vertex.z))

        self._append_line("")
        self._append_line("\t\t} ")

        # triangles
        self._append_line("\t\tPolygonVertexIndex: *" + str(indices_count) + " {")
        self._append("\t\t\ta: ")

        for i in range(0, indices_count, 3):
            if i > 0:
                self._append(",")
            self._append("{0},{1},{2}".format(geo.indices[i + 0], geo.indices[i + 1], -geo.indices[i + 2] - 1))
        self._append_line("")
        self._append_line("\t\t} ")

        # vertex normals
        self._append_line("\t\tGeometryVersion: 124")
        self._append_line("\t\tLayerElementNormal: 0 {")
        self._append_line("\t\t\tVersion: 101")
        self._append_line("\t\t\tName: \"\"")
        self._append_line("\t\t\tMappingInformationType: \"ByPolygonVertex\"")
        self._append_line("\t\t\tReferenceInformationType: \"Direct\"")

        self._append_line("\t\t\tNormals: *" + str(indices_count * 3) + " {")
        self._append("\t\t\t\ta: ")

        for i in range(0, indices_count, 3):
            if i > 0:
                self._append(",")
            v0 = geo.vertices[geo.indices[i + 0]]
            v1 = geo.vertices[geo.indices[i + 1]]
            v2 = geo.vertices[geo.indices[i + 2]]
            self._append("{0},{1},{2},".format(v0.nx, v0.ny, v0.nz))
            self._append("{0},{1},{2},".format(v1.nx, v1.ny, v1.nz))
            self._append("{0},{1},{2},".format(v2.nx, v2.ny, v2.nz))

        self._append_line("")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")

        # UV coordinates
        self._append_line("\t\tLayerElementUV: 0 {")
        self._append_line("\t\t\tVersion: 101")
        self._append_line("\t\t\tName: \"map1\"")
        self._append_line("\t\t\tMappingInformationType: \"ByPolygonVertex\"")
        self._append_line("\t\t\tReferenceInformationType: \"IndexToDirect\"")
        self._append_line("\t\t\tUV: *" + str(vertices_count * 2) + " {")
        self._append("\t\t\t\ta: ")

        for i, vertex in enumerate(geo.vertices):
            if i > 0:
                self._append(",")
            self._append("{0},{1}".format(vertex.u, vertex.v))

        self._append_line("")
        self._append_line("\t\t\t\t}")

        # UV indices
        self._append_line("\t\t\tUVIndex: *" + str(indices_count) + " {")
        self._append("\t\t\t\ta: ")

        for i in range(0, indices_count, 3):
            if i > 0:
                self._append(",")

            self._append("{0},{1},{2}".format(geo.indices[i + 0], geo.indices[i + 1], geo.indices[i + 2]))

        self._append_line("")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")

        self._append_line("\t\tLayerElementMaterial: 0 {")
        self._append_line("\t\t\tVersion: 101")
        self._append_line("\t\t\tName: \"\"")
        self._append_line("\t\t\tMappingInformationType: \"AllSame\"")
        self._append_line("\t\t\tReferenceInformationType: \"IndexToDirect\"")
        self._append_line("\t\t\tMaterials: *1 {")
        self._append_line("\t\t\t\ta: 0")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")

        self._append_line("\t\tLayer: 0 {")
        self._append_line("\t\t\tVersion: 101")
        self._append_line("\t\t\tLayerElement:  {")
        self._append_line("\t\t\t\tType: \"LayerElementNormal\"")
        self._append_line("\t\t\t\tTypedIndex: 0")
        self._append_line("\t\t\t}")
        self._append_line("\t\t\tLayerElement:  {")
        self._append_line("\t\t\t\tType: \"LayerElementMaterial\"")
        self._append_line("\t\t\t\tTypedIndex: 0")
        self._append_line("\t\t\t}")
        self._append_line("\t\t\tLayerElement:  {")
        self._append_line("\t\t\t\tType: \"LayerElementUV\"")
        self._append_line("\t\t\t\tTypedIndex: 0")
        self._append_line("\t\t\t}")
        self._append_line("\t\t}")

        self._append_line("\t}")

        # model (transform)
        uid = fbx_generate_id()
        self._append_line("\tModel: " + uid + ", \"Model::" + mesh_name + "\", \"Mesh\" {")
        self._append_line("\t\tVersion: 232")
        self._append_line("\t\tProperties70:  {")

        # EULER_XYZ = 0
        # EULER_XZY = 1
        # EULER_YZX = 2
        # EULER_YXZ = 3
        # EULER_ZXY = 4
        # EULER_ZYX = 5
        self._append_line("\t\t\tP: \"RotationOrder\", \"enum\", \"\", \"\",0")
        self._append_line("\t\t\tP: \"RotationActive\", \"bool\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"InheritType\", \"enum\", \"\", \"\",1")
        self._append_line("\t\t\tP: \"ScalingMax\", \"Vector3D\", \"Vector\", \"\",0,0,0")
        self._append_line("\t\t\tP: \"DefaultAttributeIndex\", \"int\", \"Integer\", \"\",0")

        self._append_line(
            "\t\t\tP: \"Lcl Translation\", \"Lcl Translation\", \"\", \"A\",{0},{1},{2}".format(t.px, t.py, t.pz))
        self._append_line(
            "\t\t\tP: \"Lcl Rotation\", \"Lcl Rotation\", \"\", \"A\",{0},{1},{2}".format(t.rx, t.ry, t.rz))
        self._append_line(
            "\t\t\tP: \"Lcl Scaling\", \"Lcl Scaling\", \"\", \"A\",{0},{1},{2}".format(t.sx, t.sy, t.sz))

        self._append_line("\t\t\tP: \"currentUVSet\", \"KString\", \"\", \"U\", \"map1\"")
        self._append_line("\t\t}")
        self._append_line("\t\tShading: T")
        self._append_line("\t\tCulling: \"CullingOff\"")

        self._append_line("\t}")

        if material_id != 0:
            self.connections.append((material_id, uid))

        self.connections.append((uid, parent_id))
        self.connections.append((geom_id, uid))

        return uid

    def finalize(self) -> str:
        self._end_objects()
        self._append_line("; Object connections")
        self._append_line(";------------------------------------------------------------------")
        self._append_line("")
        self._append_line("Connections:  {")

        for node_id, parent_id in self.connections:
            self._append_line("\tC: \"OO\",{0},{1}".format(node_id, parent_id))

        for node_id, parent_id, name in self.named_connections:
            self._append_line("\tC: \"OP\",{0},{1}, \"{2}\"".format(node_id, parent_id, name))

        self._append_line("}")
        return ''.join(self.text_chunks)
