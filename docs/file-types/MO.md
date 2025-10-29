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
│  Vertex Data                      (faces_count × 3 × 48 bytes)  │
├─────────────────────────────────────────────────────────────────┤
│  Padding                          (4 bytes)                     │
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

Object names follow special prefixes that indicate their purpose:

| Prefix | Description                          | Rendered |
|--------|--------------------------------------|----------|
| `b`    | Border/collision geometry            | No       |
| `s`    | Skybox geometry                      | No       |
| `t`    | Timer trigger zones                  | No       |
| other  | Standard visible geometry            | Yes      |

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

## Vertex Data (48 bytes each)

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

**Total: 48 bytes (0x30) per vertex**

### Vertex Layout Summary

```
┌────────────────────────────────────────────────────────────────┐
│  Vertex (48 bytes)                                             │
├────────────┬────────────┬────────────┬────────────────────────┤
│  Position  │   Normal   │   Flags    │   UV + Unknown         │
│  X, Y, Z   │  NX,NY,NZ  │  (uint32)  │   U, V, _a, _b         │
│  12 bytes  │  12 bytes  │  4 bytes   │   20 bytes             │
└────────────┴────────────┴────────────┴────────────────────────┘
```

---

## Padding (4 bytes)

Offset: After vertex data.

4 bytes of padding/alignment before texture metadata.

---

## Texture Metadata (300 bytes each)

Offset: After padding.

Array of `textures_count` entries.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                                                               +
|                                                               |
+                                                               +
~                   Texture File Path (300 bytes)               ~
~                     Null-terminated ASCII                     ~
|                                                               |
+                                                               +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Offset | Size | Type      | Description                       |
|--------|------|-----------|-----------------------------------|
| 0x00   | 300  | char[300] | Texture file path (null-term)     |

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
VERTICES_SIZE         = faces_count × 3 × 48

PADDING_OFFSET        = VERTICES_OFFSET + VERTICES_SIZE
PADDING_SIZE          = 4

TEXTURES_OFFSET       = PADDING_OFFSET + PADDING_SIZE
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

// 4. Read all vertices
MoVertex vertices[header.faces_count * 3];
fread(vertices, 48, header.faces_count * 3, file);

// 5. Skip padding
fseek(file, 4, SEEK_CUR);

// 6. Read texture paths
MoTextureMeta textures[header.textures_count];
fread(textures, 300, header.textures_count, file);
```

---

## Notes

- Geometry is stored as **triangle lists** (not strips or fans)
- Each face consists of exactly 3 vertices
- Objects reference vertices via an offset into the global vertex array
- The scale factor commonly used is `0.15` when rendering
- The model is mirrored in X-axis
- Object names starting with `b_` (borders), `s_` (skybox), or `t` (timer hitboxes) are typically hidden during rendering
