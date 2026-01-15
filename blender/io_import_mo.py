# SPDX-License-Identifier: GPL-3.0-or-later
# MO File Importer for Blender 5.0
# Imports .mo 3D model files from Maluch Sim 2

bl_info = {
    "name": "Maluch Sim 2 MO Format",
    "author": "Adrian Michalski (MicMic)",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "File > Import > Maluch Sim 2 (.mo)",
    "description": "Import MO model files from Maluch Sim 2",
    "category": "Import-Export",
}

import bpy
import struct
import os
from bpy.props import StringProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Vector


# ============================================================================
# CDF File Format (Car Definition File)
# ============================================================================

class CdfFile:
    """Parser for .cdf car definition files.
    
    The CDF file contains car physics and wheel position data.
    First 48 bytes contain 4 wheel positions (12 bytes each = 3 floats XYZ).
    
    Wheel order:
    - 0: Front-Left
    - 1: Front-Right
    - 2: Rear-Left
    - 3: Rear-Right
    """
    
    WHEEL_NAMES = ["wheel_front_left", "wheel_front_right", 
                   "wheel_rear_left", "wheel_rear_right"]
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.wheel_positions = []
    
    def parse(self):
        """Parse wheel positions from CDF file"""
        if not os.path.exists(self.filepath):
            print(f"CDF file not found: {self.filepath}")
            return False
        
        with open(self.filepath, 'rb') as f:
            data = f.read(48)  # 4 wheels × 3 floats × 4 bytes
        
        if len(data) < 48:
            print(f"CDF file too small: {len(data)} bytes")
            return False
        
        for i in range(4):
            x, y, z = struct.unpack('<3f', data[i*12:(i+1)*12])
            self.wheel_positions.append((x, y, z))
            print(f"  {self.WHEEL_NAMES[i]}: ({x:.3f}, {y:.3f}, {z:.3f})")
        
        return True
    
    @staticmethod
    def find_for_mo_file(mo_filepath):
        """Find .cdf file corresponding to a .mo file"""
        directory = os.path.dirname(mo_filepath)
        base_name = os.path.splitext(os.path.basename(mo_filepath))[0]
        
        # Try exact match first
        cdf_path = os.path.join(directory, base_name + ".cdf")
        if os.path.exists(cdf_path):
            return cdf_path
        
        # Try case-insensitive search
        for filename in os.listdir(directory):
            if filename.lower().endswith('.cdf'):
                return os.path.join(directory, filename)
        
        return None


# ============================================================================
# MO File Format Structures
# ============================================================================

MO_MAGIC = b"MOFILE00"
HEADER_SIZE = 60
OBJECT_META_SIZE = 160
TEXTURED_FACES_SIZE = 8
VERTEX_SIZE = 44  # NOTE: Spec says 48, but actual files use 44 bytes
TEXTURE_META_SIZE = 300


class MoHeader:
    """MO file header (60 bytes)"""
    
    def __init__(self):
        self.magic = b""
        self.objects_count = 0
        self.faces_count = 0
        self.textures_count = 0
        self.reserved = []
    
    @classmethod
    def read(cls, file):
        header = cls()
        header.magic = file.read(8)
        
        if header.magic != MO_MAGIC:
            raise ValueError(f"Invalid MO file magic: {header.magic}")
        
        data = struct.unpack("<3I", file.read(12))
        header.objects_count = data[0]
        header.faces_count = data[1]
        header.textures_count = data[2]
        
        # Skip reserved 40 bytes (10 × uint32)
        header.reserved = struct.unpack("<10I", file.read(40))
        
        return header


class ObjectMeta:
    """Object metadata (160 bytes per object)"""
    
    def __init__(self):
        self.name = ""
        self.vertex_offset = 0
        self.faces_count = 0
        self.unknown_floats = []
    
    @classmethod
    def read(cls, file):
        obj = cls()
        
        # Read 128-byte null-terminated name
        name_bytes = file.read(128)
        obj.name = name_bytes.split(b'\x00')[0].decode('latin-1', errors='replace')
        
        data = struct.unpack("<2I6f", file.read(32))
        obj.vertex_offset = data[0]
        obj.faces_count = data[1]
        obj.unknown_floats = data[2:8]  # Possibly bounding box/transform
        
        return obj
    
    def should_render(self):
        """Check if object should be rendered based on naming convention
        
        Hidden objects (not rendered):
        - b_*     = invisible border/collision geometry
        - ts_time = timer start hitbox
        - tm_time = timer checkpoint hitbox
        
        Note: s_* (skybox) objects ARE visible and rendered.
        """
        if not self.name:
            return True
        name_lower = self.name.lower()
        
        # Check for invisible border prefix
        if name_lower.startswith('b_'):
            return False
        
        # Check for timer trigger hitboxes
        if name_lower in ('ts_time', 'tm_time'):
            return False
        
        return True


class TexturedFaces:
    """Textured faces table entry (8 bytes)"""
    
    def __init__(self):
        self.object_offset = 0
        self.faces = 0
    
    @classmethod
    def read(cls, file):
        entry = cls()
        data = struct.unpack("<2I", file.read(8))
        entry.object_offset = data[0]
        entry.faces = data[1]
        return entry


class MoVertex:
    """Vertex data (44 bytes per vertex)
    
    NOTE: The spec incorrectly states 48 bytes. Actual format is 44 bytes:
    - 3 floats: position (12 bytes)
    - 3 floats: normal (12 bytes)
    - 1 uint32: flags (4 bytes)
    - 2 floats: UV (8 bytes)
    - 2 uint32: unknown (8 bytes)
    Total: 44 bytes
    """
    
    def __init__(self):
        self.position = (0.0, 0.0, 0.0)
        self.normal = (0.0, 0.0, 0.0)
        self.flags = 0
        self.uv = (0.0, 0.0)
        self.unknown_a = 0
        self.unknown_b = 0
    
    @classmethod
    def read(cls, file):
        vert = cls()
        # Format: 3f (pos) + 3f (normal) + I (flags) + 2f (uv) + 2I (unknown) = 44 bytes
        data = struct.unpack("<3f3fI2f2I", file.read(44))
        vert.position = (data[0], data[1], data[2])
        vert.normal = (data[3], data[4], data[5])
        vert.flags = data[6]
        vert.uv = (data[7], data[8])
        vert.unknown_a = data[9]
        vert.unknown_b = data[10]
        return vert


class TextureMeta:
    """Texture metadata (300 bytes per texture)
    
    Structure:
    - 4 bytes: unknown (seems always 0)
    - 296 bytes: file path (null-terminated)
    """
    
    def __init__(self):
        self.unknown = 0
        self.file_path = ""
    
    @classmethod
    def read(cls, file):
        tex = cls()
        # First 4 bytes are unknown/padding
        tex.unknown = struct.unpack("<I", file.read(4))[0]
        # Remaining 296 bytes are the path
        path_bytes = file.read(296)
        tex.file_path = path_bytes.split(b'\x00')[0].decode('latin-1', errors='replace')
        return tex


# ============================================================================
# MO File Parser
# ============================================================================

class MoFile:
    """Complete MO file parser"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.directory = os.path.dirname(filepath)
        self.header = None
        self.objects = []
        self.textured_faces = []
        self.vertices = []
        self.textures = []
    
    def parse(self):
        """Parse the MO file"""
        with open(self.filepath, 'rb') as f:
            # 1. Read header
            self.header = MoHeader.read(f)
            print(f"MO File: {self.filepath}")
            print(f"Objects: {self.header.objects_count}")
            print(f"Faces: {self.header.faces_count}")
            print(f"Textures: {self.header.textures_count}")
            
            # 2. Read object metadata
            for i in range(self.header.objects_count):
                obj = ObjectMeta.read(f)
                self.objects.append(obj)
                print(f"  Object #{i}: {obj.name} ({obj.faces_count} tris)")
            
            # 3. Read textured faces table (2D array flattened)
            total_tf_entries = self.header.objects_count * self.header.textures_count
            for _ in range(total_tf_entries):
                tf = TexturedFaces.read(f)
                self.textured_faces.append(tf)
            
            # 4. Read all vertices (faces_count × 3)
            total_vertices = self.header.faces_count * 3
            for _ in range(total_vertices):
                vert = MoVertex.read(f)
                self.vertices.append(vert)
            
            # NOTE: Spec mentions 4-byte padding here, but actual files have none
            
            # 5. Read texture metadata
            for i in range(self.header.textures_count):
                tex = TextureMeta.read(f)
                self.textures.append(tex)
                print(f"  Texture #{i}: {tex.file_path}")
    
    def get_object_texture_index(self, obj_index):
        """Get the texture index for an object"""
        tex_count = self.header.textures_count
        for t in range(tex_count):
            tf_index = obj_index * tex_count + t
            if self.textured_faces[tf_index].faces > 0:
                return t
        return 0


# ============================================================================
# Blender Import Functions
# ============================================================================

def load_texture(directory, texture_path):
    """Load a texture file and return a Blender image"""
    if not texture_path:
        return None
    
    # Normalize path separators
    texture_path = texture_path.replace('\\', os.sep).replace('/', os.sep)
    full_path = os.path.join(directory, texture_path)
    
    # Try different extensions if file not found
    if not os.path.exists(full_path):
        base, ext = os.path.splitext(full_path)
        for alt_ext in ['.dds', '.tga', '.png', '.jpg', '.bmp']:
            alt_path = base + alt_ext
            if os.path.exists(alt_path):
                full_path = alt_path
                break
    
    if os.path.exists(full_path):
        try:
            img = bpy.data.images.load(full_path)
            return img
        except Exception as e:
            print(f"Failed to load texture {full_path}: {e}")
    else:
        print(f"Texture not found: {full_path}")
    
    return None


def create_material(name, image=None):
    """Create a material with optional texture"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Create nodes
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (300, 0)
    
    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_node.location = (0, 0)
    
    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    if image:
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.location = (-300, 0)
        tex_node.image = image
        links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
        
        # Check for alpha channel
        if image.channels == 4:
            links.new(tex_node.outputs['Alpha'], bsdf_node.inputs['Alpha'])
            mat.blend_method = 'CLIP'
    
    return mat


def create_mesh_from_object(mo_file, obj_index, scale=0.15, mirror_x=True):
    """Create a Blender mesh from an MO object"""
    obj_meta = mo_file.objects[obj_index]
    
    print(f"  Creating mesh for object #{obj_index}: {obj_meta.name}")
    print(f"    vertex_offset={obj_meta.vertex_offset}, faces_count={obj_meta.faces_count}")
    
    if obj_meta.faces_count == 0:
        print(f"    WARNING: Object has 0 faces, skipping")
        return None
    
    # Calculate vertex range
    # NOTE: vertex_offset is in VERTEX units (not face units)
    vertex_offset = obj_meta.vertex_offset
    vertex_count = obj_meta.faces_count * 3
    
    print(f"    Reading {vertex_count} vertices starting at index {vertex_offset}")
    print(f"    Total vertices in file: {len(mo_file.vertices)}")
    
    # Collect vertices for this object
    vertices = []
    normals = []
    uvs = []
    
    # Track bounds for debugging
    min_pos = [float('inf')] * 3
    max_pos = [float('-inf')] * 3
    
    for i in range(vertex_count):
        vert_idx = vertex_offset + i
        if vert_idx >= len(mo_file.vertices):
            print(f"    ERROR: vertex index {vert_idx} out of range (max {len(mo_file.vertices)-1})")
            continue
        
        vert = mo_file.vertices[vert_idx]
        
        # Original coordinates (OpenGL-style: Y-up, Z-forward)
        ox = vert.position[0]
        oy = vert.position[1]
        oz = vert.position[2]
        
        # Convert to Blender coordinates (Z-up, -Y forward)
        # x_blender = x_original
        # y_blender = -z_original  
        # z_blender = y_original
        x = ox * scale
        y = -oz * scale
        z = oy * scale
        
        if mirror_x:
            x = -x
        
        vertices.append((x, y, z))
        
        # Track bounds
        min_pos[0] = min(min_pos[0], x)
        min_pos[1] = min(min_pos[1], y)
        min_pos[2] = min(min_pos[2], z)
        max_pos[0] = max(max_pos[0], x)
        max_pos[1] = max(max_pos[1], y)
        max_pos[2] = max(max_pos[2], z)
        
        # Convert normals with same transformation
        onx = vert.normal[0]
        ony = vert.normal[1]
        onz = vert.normal[2]
        
        nx = onx
        ny = -onz
        nz = ony
        
        if mirror_x:
            nx = -nx
        normals.append((nx, ny, nz))
        
        # Flip V texture coordinate (1.0 - v)
        uvs.append((vert.uv[0], 1.0 - vert.uv[1]))
    
    if not vertices:
        print(f"    ERROR: No vertices collected!")
        return None
    
    print(f"    Collected {len(vertices)} vertices")
    print(f"    Bounds: min=({min_pos[0]:.2f}, {min_pos[1]:.2f}, {min_pos[2]:.2f})")
    print(f"            max=({max_pos[0]:.2f}, {max_pos[1]:.2f}, {max_pos[2]:.2f})")
    
    # Create faces (triangle list)
    faces = []
    for i in range(0, len(vertices), 3):
        if i + 2 < len(vertices):
            if mirror_x:
                # Reverse winding order when mirroring
                faces.append((i, i + 2, i + 1))
            else:
                faces.append((i, i + 1, i + 2))
    
    print(f"    Created {len(faces)} faces")
    
    # Create mesh
    mesh_name = obj_meta.name or f"MO_Object_{obj_index}"
    mesh = bpy.data.meshes.new(name=mesh_name)
    
    try:
        mesh.from_pydata(vertices, [], faces)
        print(f"    Mesh created successfully: {len(mesh.vertices)} verts, {len(mesh.polygons)} polys")
    except Exception as e:
        print(f"    ERROR creating mesh: {e}")
        return None
    
    # Add UV layer
    if uvs and len(mesh.polygons) > 0:
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for face in mesh.polygons:
            for loop_idx in face.loop_indices:
                vert_idx = mesh.loops[loop_idx].vertex_index
                if vert_idx < len(uvs):
                    uv_layer.data[loop_idx].uv = uvs[vert_idx]
    
    # Set custom normals (only if mesh has polygons)
    if len(mesh.polygons) > 0 and len(normals) == len(mesh.vertices):
        try:
            mesh.normals_split_custom_set_from_vertices(normals)
        except Exception as e:
            print(f"    Warning: Could not set custom normals: {e}")
    
    mesh.update()
    result = mesh.validate(verbose=True)
    if result:
        print(f"    Mesh validation found issues (corrected)")
    
    return mesh


def import_mo_file(context, filepath, scale=0.15, mirror_x=True, 
                   import_hidden=False, import_textures=True, import_cdf=True):
    """Main import function"""
    
    print(f"\n{'='*60}")
    print(f"Importing MO file: {filepath}")
    print(f"Scale: {scale}, Mirror X: {mirror_x}")
    print(f"Import hidden: {import_hidden}, Import textures: {import_textures}")
    print(f"Import CDF (wheels): {import_cdf}")
    print(f"{'='*60}\n")
    
    # Parse the MO file
    mo_file = MoFile(filepath)
    try:
        mo_file.parse()
    except Exception as e:
        import traceback
        print(f"Error parsing MO file: {e}")
        traceback.print_exc()
        return {'CANCELLED'}
    
    print(f"\nParsed successfully:")
    print(f"  Objects: {len(mo_file.objects)}")
    print(f"  Vertices: {len(mo_file.vertices)}")
    print(f"  Textures: {len(mo_file.textures)}")
    print(f"  Textured faces entries: {len(mo_file.textured_faces)}")
    
    # Try to find and parse CDF file for wheel positions
    cdf_file = None
    if import_cdf:
        cdf_path = CdfFile.find_for_mo_file(filepath)
        if cdf_path:
            print(f"\nFound CDF file: {cdf_path}")
            cdf_file = CdfFile(cdf_path)
            if not cdf_file.parse():
                cdf_file = None
        else:
            print(f"\nNo CDF file found (wheel positions not available)")
    
    # Debug: print first few vertices
    if mo_file.vertices:
        print(f"\nFirst 3 vertices (raw positions):")
        for i, v in enumerate(mo_file.vertices[:3]):
            print(f"  [{i}] pos=({v.position[0]:.2f}, {v.position[1]:.2f}, {v.position[2]:.2f})")
    
    # Load textures
    loaded_textures = []
    materials = []
    
    if import_textures:
        for i, tex_meta in enumerate(mo_file.textures):
            img = load_texture(mo_file.directory, tex_meta.file_path)
            loaded_textures.append(img)
            
            mat_name = os.path.splitext(os.path.basename(tex_meta.file_path))[0]
            if not mat_name:
                mat_name = f"MO_Material_{i}"
            mat = create_material(mat_name, img)
            materials.append(mat)
    
    # Create a parent empty for organization
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    parent_empty = bpy.data.objects.new(base_name, None)
    parent_empty.empty_display_type = 'PLAIN_AXES'
    context.collection.objects.link(parent_empty)
    
    print(f"\nCreating meshes...")
    
    # Create meshes for each object
    imported_count = 0
    skipped_count = 0
    wheel_object = None  # Track the wheel object for cloning
    
    for obj_idx, obj_meta in enumerate(mo_file.objects):
        # Skip hidden objects unless requested
        if not import_hidden and not obj_meta.should_render():
            print(f"Skipping hidden object: {obj_meta.name}")
            skipped_count += 1
            continue
        
        mesh = create_mesh_from_object(mo_file, obj_idx, scale, mirror_x)
        if mesh is None:
            print(f"  Failed to create mesh for {obj_meta.name}")
            continue
        
        # Create object
        obj = bpy.data.objects.new(mesh.name, mesh)
        context.collection.objects.link(obj)
        obj.parent = parent_empty
        
        # Assign material
        if import_textures and materials:
            tex_idx = mo_file.get_object_texture_index(obj_idx)
            if tex_idx < len(materials):
                obj.data.materials.append(materials[tex_idx])
        
        # Track wheel object for later cloning
        if obj_meta.name.lower() == 'wheel':
            wheel_object = obj
        
        imported_count += 1
    
    # Clone wheel object to 4 positions if CDF was loaded
    if cdf_file and wheel_object:
        print(f"\nCloning wheel to 4 positions from CDF...")
        
        # Hide the original centered wheel
        wheel_object.hide_set(True)
        wheel_object.hide_render = True
        wheel_object.name = "wheel_template"
        
        for i, (wx, wy, wz) in enumerate(cdf_file.wheel_positions):
            wheel_name = CdfFile.WHEEL_NAMES[i]
            
            # Create a copy of the wheel mesh
            new_mesh = wheel_object.data.copy()
            new_mesh.name = wheel_name
            
            # Create new object
            new_wheel = bpy.data.objects.new(wheel_name, new_mesh)
            context.collection.objects.link(new_wheel)
            new_wheel.parent = parent_empty
            
            # Copy materials
            for mat in wheel_object.data.materials:
                new_wheel.data.materials.append(mat)
            
            # Convert CDF coordinates to Blender (same as vertex conversion)
            # Original: Y-up, Z-forward → Blender: Z-up, -Y forward
            # Note: Ignoring Y (height) from CDF - wheels placed at Z=0
            bx = wx * scale
            by = -wz * scale
            bz = 0.0  # Ignore ride height, place wheels at ground level
            
            if mirror_x:
                bx = -bx
            
            new_wheel.location = (bx, by, bz)
            
            # Mirror wheels so inside of rim faces the car body (suspension)
            # Left wheels (negative X in original): mirror to face right
            # Right wheels (positive X in original): mirror to face left
            is_left_wheel = wx < 0
            if is_left_wheel:
                new_wheel.scale.x = -1.0  # Left wheels: flip to face car center
            # Right wheels keep default orientation (inside already faces car center)
            
            print(f"  {wheel_name}: CDF({wx:.3f}, {wy:.3f}, {wz:.3f}) → Blender({bx:.3f}, {by:.3f}, {bz:.3f}), mirror={is_left_wheel}")
            
            imported_count += 1
    
    # Select the parent
    parent_empty.select_set(True)
    context.view_layer.objects.active = parent_empty
    
    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE")
    print(f"  Imported: {imported_count} objects")
    print(f"  Skipped (hidden): {skipped_count} objects")
    if cdf_file and wheel_object:
        print(f"  Wheels cloned: 4 (from CDF)")
    print(f"{'='*60}\n")
    
    # Frame selected in viewport
    if imported_count > 0:
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'area': area, 'region': region}
                        try:
                            bpy.ops.view3d.view_selected(override)
                        except:
                            pass
                        break
    
    return {'FINISHED'}


# ============================================================================
# Blender Operator
# ============================================================================

class IMPORT_OT_mo(bpy.types.Operator, ImportHelper):
    """Import a Maluch Sim 2 MO file"""
    bl_idname = "import_scene.mo"
    bl_label = "Import MO"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".mo"
    
    filter_glob: StringProperty(
        default="*.mo",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    scale: FloatProperty(
        name="Scale",
        description="Scale factor for imported geometry",
        default=1.0,
        min=0.001,
        max=100.0,
    )
    
    mirror_x: BoolProperty(
        name="Mirror X-Axis",
        description="Mirror the model along the X-axis",
        default=True,
    )
    
    import_hidden: BoolProperty(
        name="Import Hidden Objects",
        description="Import collision, skybox, and trigger objects",
        default=False,
    )
    
    import_textures: BoolProperty(
        name="Import Textures",
        description="Load and assign textures to materials",
        default=True,
    )
    
    import_cdf: BoolProperty(
        name="Import CDF (Wheel Positions)",
        description="Load .cdf file and clone wheels to correct positions",
        default=True,
    )
    
    def execute(self, context):
        return import_mo_file(
            context,
            self.filepath,
            scale=self.scale,
            mirror_x=self.mirror_x,
            import_hidden=self.import_hidden,
            import_textures=self.import_textures,
            import_cdf=self.import_cdf,
        )
    
    def draw(self, context):
        layout = self.layout
        
        layout.prop(self, "scale")
        layout.prop(self, "mirror_x")
        
        layout.separator()
        layout.label(text="Options:")
        layout.prop(self, "import_hidden")
        layout.prop(self, "import_textures")
        layout.prop(self, "import_cdf")


# ============================================================================
# Debug / Test Functions
# ============================================================================

def test_parse_only(filepath):
    """
    Test parsing without importing into Blender.
    Usage in Blender Python Console:
        from io_import_mo import test_parse_only
        test_parse_only("/path/to/file.mo")
    """
    mo_file = MoFile(filepath)
    mo_file.parse()
    
    print(f"\n--- Parse Summary ---")
    print(f"Objects: {len(mo_file.objects)}")
    for i, obj in enumerate(mo_file.objects):
        print(f"  [{i}] {obj.name}: offset={obj.vertex_offset}, faces={obj.faces_count}")
    
    print(f"\nVertices: {len(mo_file.vertices)}")
    if mo_file.vertices:
        # Calculate global bounds
        min_x = min(v.position[0] for v in mo_file.vertices)
        max_x = max(v.position[0] for v in mo_file.vertices)
        min_y = min(v.position[1] for v in mo_file.vertices)
        max_y = max(v.position[1] for v in mo_file.vertices)
        min_z = min(v.position[2] for v in mo_file.vertices)
        max_z = max(v.position[2] for v in mo_file.vertices)
        print(f"  Bounds X: {min_x:.2f} to {max_x:.2f}")
        print(f"  Bounds Y: {min_y:.2f} to {max_y:.2f}")
        print(f"  Bounds Z: {min_z:.2f} to {max_z:.2f}")
    
    print(f"\nTextures: {len(mo_file.textures)}")
    for i, tex in enumerate(mo_file.textures):
        print(f"  [{i}] {tex.file_path}")
    
    return mo_file


def test_import(filepath, scale=1.0, import_cdf=True):
    """
    Quick import test with default scale of 1.0 for debugging.
    Usage in Blender Python Console:
        from io_import_mo import test_import
        test_import("/path/to/file.mo")
    """
    import bpy
    return import_mo_file(
        bpy.context, 
        filepath, 
        scale=scale, 
        mirror_x=True,
        import_hidden=True,  # Import everything for debugging
        import_textures=False,  # Skip textures for faster testing
        import_cdf=import_cdf,  # Clone wheels from CDF
    )


# ============================================================================
# Registration
# ============================================================================

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_mo.bl_idname, text="Maluch Sim 2 (.mo)")


def register():
    bpy.utils.register_class(IMPORT_OT_mo)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_mo)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
