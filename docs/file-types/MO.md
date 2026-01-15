# MO File Format Specification

The `.mo` file format is a 3D model container format used by **Maluch Sim 2** (MS2).
It stores mesh geometry, object list, texture assignments, and vertex data for game assets - cars and tracks.

## File Signature

All MO files begin with the 8-byte ASCII magic string: `MOFILE00`

---

## File Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         MO FILE                                 │
├─────────────────────────────────────────────────────────────────┤
│  Header                           (60 bytes)                    │
├─────────────────────────────────────────────────────────────────┤
│  Object Metadata Array            (objects_count × 160 bytes)   │
├─────────────────────────────────────────────────────────────────┤
│  Textured Faces Table             (objects × textures × 8 bytes)│
├─────────────────────────────────────────────────────────────────┤
│  Vertex Data                      (faces_count × 3 × 44 bytes)  │
├─────────────────────────────────────────────────────────────────┤
│  Texture Metadata Array           (textures_count × 300 bytes)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Header Structure (60 bytes)

Offset: `0x00`

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                         Magic (8 bytes)                       +
|                        "MOFILE00"                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Objects Count                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Faces Count                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Textures Count                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                     Reserved (40 bytes)                       +
|                          10 × uint32                          |
+                                                               +
|                                                               |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size | Type      | Description                              |
|--------|------|-----------|------------------------------------------|
| 0x00   | 8    | char[8]   | Magic signature `"MOFILE00"`             |
| 0x08   | 4    | uint32    | Number of objects/meshes in file         |
| 0x0C   | 4    | uint32    | Total number of triangular faces         |
| 0x10   | 4    | uint32    | Number of textures referenced            |
| 0x14   | 40   | uint32[10]| Reserved/unknown                         |

**Total: 60 bytes (0x3C)**

---

## Object Metadata (160 bytes each)

Offset: `0x3C` (immediately after header)

Array of `objects_count` entries.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                                                               +
~                     Object Name (128 bytes)                   ~
~                    Null-terminated ASCII                      ~
|                                                               |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Vertex Offset (index)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Faces Count                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unknown A (float)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unknown B (float)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unknown C (float)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unknown D (float)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unknown E (float)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Unknown F (float)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size | Type      | Description                              |
|--------|------|-----------|------------------------------------------|
| 0x00   | 128  | char[128] | Object name (null-terminated)            |
| 0x80   | 4    | uint32    | Vertex offset in vertex array            |
| 0x84   | 4    | uint32    | Number of faces for this object          |
| 0x88   | 24   | float[6]  | Unknown (possibly bounding box/transform)|

**Total: 160 bytes (0xA0) per object**

### Object Naming Conventions

Object names follow specific prefixes and patterns depending on whether the file contains a car or track model. See the dedicated sections below for details:

- [Car Object Naming](#car-object-naming)
- [Track Object Naming](#track-object-naming)

---

## Textured Faces Table (8 bytes each)

Offset: After object metadata section.

This is a 2D table stored as a flat array: `[objects_count][textures_count]`

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Object Offset                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Faces Count                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size | Type   | Description                                  |
|--------|------|--------|----------------------------------------------|
| 0x00   | 4    | uint32 | Object offset reference                      |
| 0x04   | 4    | uint32 | Number of faces using this texture           |

**Total: 8 bytes per entry**
**Array size: `objects_count × textures_count` entries**

This table maps which faces of each object use which texture.

---

## Vertex Data (44 bytes each)

Offset: After textured faces table.

Stored as triangle lists: `faces_count × 3` vertices total.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         X (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Y (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         Z (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        NX (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        NY (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        NZ (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Flags (uint32)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         U (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                         V (float)                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Unknown A (uint32)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Unknown B (uint32)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size | Type   | Description                     |
|--------|------|--------|---------------------------------|
| 0x00   | 4    | float  | X position                      |
| 0x04   | 4    | float  | Y position                      |
| 0x08   | 4    | float  | Z position                      |
| 0x0C   | 4    | float  | Normal X component              |
| 0x10   | 4    | float  | Normal Y component              |
| 0x14   | 4    | float  | Normal Z component              |
| 0x18   | 4    | uint32 | Vertex flags (purpose unknown)  |
| 0x1C   | 4    | float  | U texture coordinate            |
| 0x20   | 4    | float  | V texture coordinate            |
| 0x24   | 4    | uint32 | Unknown A                       |
| 0x28   | 4    | uint32 | Unknown B                       |

**Total: 44 bytes (0x2C) per vertex**

### Vertex Layout Summary

```
┌────────────────────────────────────────────────────────────────┐
│  Vertex (44 bytes)                                             │
├────────────┬────────────┬────────────┬────────────────────────┤
│  Position  │   Normal   │   Flags    │   UV + Unknown         │
│  X, Y, Z   │  NX,NY,NZ  │  (uint32)  │   U, V, _a, _b         │
│  12 bytes  │  12 bytes  │  4 bytes   │   16 bytes             │
└────────────┴────────────┴────────────┴────────────────────────┘
```

---

## Texture Metadata (300 bytes each)

Offset: After vertex data.

Array of `textures_count` entries.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Unknown (uint32)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                                                               +
~                   Texture File Path (296 bytes)               ~
~                     Null-terminated ASCII                     ~
|                                                               |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size | Type      | Description                       |
|--------|------|-----------|-----------------------------------|
| 0x00   | 4    | uint32    | Unknown (always 0 in observed files) |
| 0x04   | 296  | char[296] | Texture file path (null-term)     |

**Total: 300 bytes (0x12C) per texture**

Texture paths are relative to the model file's directory.

---

## Complete File Offset Calculation

```
HEADER_OFFSET         = 0x00
HEADER_SIZE           = 60

OBJECTS_OFFSET        = HEADER_SIZE
OBJECTS_SIZE          = objects_count × 160

TEXTURED_FACES_OFFSET = OBJECTS_OFFSET + OBJECTS_SIZE
TEXTURED_FACES_SIZE   = objects_count × textures_count × 8

VERTICES_OFFSET       = TEXTURED_FACES_OFFSET + TEXTURED_FACES_SIZE
VERTICES_SIZE         = faces_count × 3 × 44

TEXTURES_OFFSET       = VERTICES_OFFSET + VERTICES_SIZE
TEXTURES_SIZE         = textures_count × 300
```

---

## Data Types Reference

| Type   | Size    | Description                    |
|--------|---------|--------------------------------|
| char   | 1 byte  | ASCII character                |
| uint32 | 4 bytes | Unsigned 32-bit integer (LE)   |
| float  | 4 bytes | 32-bit IEEE 754 float (LE)     |

All multi-byte values are stored in **little-endian** byte order.

---

## Example Parser Pseudocode

```c
// 1. Read header
MoHeader header;
fread(&header, 60, 1, file);

// 2. Read object metadata
ObjectMeta objects[header.objects_count];
fread(objects, 160, header.objects_count, file);

// 3. Read textured faces table
MoTexturedFaces tf[header.objects_count * header.textures_count];
fread(tf, 8, header.objects_count * header.textures_count, file);

// 4. Read all vertices (44 bytes each)
MoVertex vertices[header.faces_count * 3];
fread(vertices, 44, header.faces_count * 3, file);

// 5. Read texture metadata
MoTextureMeta textures[header.textures_count];
fread(textures, 300, header.textures_count, file);
```

---

## Notes

- Geometry is stored as **triangle lists** (not strips or fans)
- Each face consists of exactly 3 vertices
- Objects reference vertices via an offset into the global vertex array
- The model is mirrored in X-axis

---

## Car Object Naming

Car `.mo` files use specific object names to define different parts of the vehicle. The game engine recognizes these names and applies special rendering or behavior.

### Visible Objects

| Object Name | Description |
|-------------|-------------|
| `body` | Main car body mesh. The game applies **reflections** to this object. |
| `down` | Chassis/undercarriage (Polish: "podwozie"). Rendered **without reflections**. |
| `wheel` | Wheel mesh. Must be **centered at origin**. The game clones this mesh 4 times and positions each wheel according to the `.cdf` configuration file. |
| `mirror1`, `mirror2` | Side mirrors. |
| `matricula_f` | Front number plate plane. The game applies a **custom number plate texture** at runtime. |
| `matricula_r` | Rear number plate plane. The game applies a **custom number plate texture** at runtime. |

### Light Sprite Positions

These objects define the position and size of light sprites. The mesh geometry determines where the sprite appears and how large it is.

| Prefix | Description |
|--------|-------------|
| `ls_*` | **Stop light** (brake light) sprite position and size. Example: `ls_LeftStop`, `ls_RightStop` |
| `lr_*` | **Reverse light** sprite position and size. Example: `lr_ReverseLight` |

### Example Car Object List

```
body            → Main body with reflections
down            → Undercarriage, no reflections
wheel           → Single wheel (cloned 4×)
ls_LeftStop     → Left brake light sprite
ls_RightStop    → Right brake light sprite
lr_ReverseLight → Reverse light sprite
mirror1         → Left side mirror
mirror2         → Right side mirror
matricula_f     → Front number plate
matricula_r     → Rear number plate
```

---

## Track Object Naming

Track `.mo` files use prefixes to categorize terrain, objects, and invisible collision/trigger geometry.

### Ground Objects (Shadow Map Applied)

These objects receive the baked shadow map texture overlay.

| Prefix | Description |
|--------|-------------|
| `gg*` | **Grass** ground with collisions. Example: `gg_field`, `gg_park` |
| `gr*` | **Road** ground with collisions (main driving surface). Example: `gr_main`, `gr_highway` |
| `gs*` | **Road sides** with collisions — ditches, slopes, curbs. Example: `gs_ditch`, `gs_slope` |

### Background Objects

| Prefix | Description |
|--------|-------------|
| `h_*` | **Background terrain** objects (distant hills, horizons). Example: `h_mountains` |

### Other Visible Objects (No Shadow Map)

| Prefix | Description |
|--------|-------------|
| `_*` | General visible objects that don't receive shadow maps. Buildings, trees, props, etc. Example: `_house`, `_tree01` |

### Special Objects

| Prefix | Description |
|--------|-------------|
| `s_*` | **Skybox** geometry. Moves with the camera to create infinite sky illusion. |

### Invisible Objects (Collision & Triggers)

These objects are **not rendered** but define game logic boundaries.

| Object Name | Description |
|-------------|-------------|
| `b_*` | **Invisible borders** — collision walls that prevent the player from leaving the track. Example: `b_wall`, `b_fence` |
| `ts_time` | **Timer start** hitbox — triggers the race timer to begin when the player enters. |
| `tm_time` | **Timer checkpoint** hitbox — checkpoint for lap timing. |

### Example Track Object List

```
gr_main         → Main road surface (collisions, shadows)
gr_junction     → Road junction
gs_curb         → Road curb/edge
gs_ditch        → Ditch beside road
gg_grass01      → Grass field
gg_park         → Park grass area
h_hills         → Background hills
_building01     → Visible building
_tree_oak       → Oak tree prop
_fence          → Visible fence
s_sky           → Skybox (moves with camera)
b_border_left   → Invisible left boundary
b_border_right  → Invisible right boundary
ts_time         → Start line timer trigger
tm_time         → Checkpoint timer trigger
```

### Summary Table

| Category | Prefix/Name | Rendered | Shadow Map | Collisions |
|----------|-------------|----------|------------|------------|
| Ground - Grass | `gg*` | ✅ Yes | ✅ Yes | ✅ Yes |
| Ground - Road | `gr*` | ✅ Yes | ✅ Yes | ✅ Yes |
| Ground - Sides | `gs*` | ✅ Yes | ✅ Yes | ✅ Yes |
| Background | `h_*` | ✅ Yes | ❌ No | ❌ No |
| Props/Objects | `_*` | ✅ Yes | ❌ No | Varies |
| Skybox | `s_*` | ✅ Yes | ❌ No | ❌ No |
| Borders | `b_*` | ❌ No | ❌ No | ✅ Yes |
| Timer Start | `ts_time` | ❌ No | ❌ No | Trigger |
| Timer Checkpoint | `tm_time` | ❌ No | ❌ No | Trigger |
