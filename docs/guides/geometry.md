# Parametric Geometry

Elementa's geometry system is built on top of the [gmsh](https://gmsh.info/) OpenCASCADE kernel, wrapped by `ElementaCAD`.

---

## Parameters

Before creating geometry, define symbolic parameters in **Definitions → Parameters**.

```
Name    Expression   Description
W       0.1          Width (m)
H       0.05         Height (m)
r       W/4          Radius
```

All geometry dimension fields accept expressions that reference these parameters. Parameter expressions may use:

- Arithmetic: `+`, `-`, `*`, `/`, `**`
- Standard math functions: `sin`, `cos`, `sqrt`, `exp`, `log`, `pi`, `e`, …
- Other parameters: `W/2`, `2*r`, `H + gap`

Parameters are resolved with full dependency tracking — you can define `gap = W * 0.1` and then use `gap` elsewhere.

---

## 2-D Primitives

### Rectangle

A centred rectangle with specified width and height.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `dx` | Width | `1.0` |
| `dy` | Height | `1.0` |
| `cx` | Centre X | `0.0` |
| `cy` | Centre Y | `0.0` |

Boundaries are automatically tagged as `<name>_edge_0` … `<name>_edge_3`.

### Disk (Ellipse)

An elliptical disk.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `rx` | Semi-axis X | `0.5` |
| `ry` | Semi-axis Y | `0.5` |
| `cx` | Centre X | `0.0` |
| `cy` | Centre Y | `0.0` |

### Polygon

An arbitrary closed polygon defined by a list of vertices.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `points` | List of `(x, y)` tuples | `[(0,0),(1,0),(0.5,0.8)]` |

Example expression: `[(0,0), (W,0), (W/2, H)]`

---

## 3-D Primitives

### Box

| Parameter | Description | Default |
|-----------|-------------|---------|
| `dx`, `dy`, `dz` | Dimensions | `1.0` each |
| `cx`, `cy`, `cz` | Centre | `0.0` each |

Faces are tagged `<name>_face_0` … `<name>_face_5`.

### Sphere

| Parameter | Description | Default |
|-----------|-------------|---------|
| `r` | Radius | `0.5` |
| `cx`, `cy`, `cz` | Centre | `0.0` each |

### Cylinder

| Parameter | Description | Default |
|-----------|-------------|---------|
| `r` | Radius | `0.2` |
| `h` | Height | `1.0` |
| `cx`, `cy`, `cz` | Base centre | `0.0` each |

---

## Boolean Operations

Boolean operations combine multiple primitives into a new shape. The input primitives are consumed (removed from the model tree) and replaced by the result.

### Union

Merges two or more shapes into a single domain.

```
result = A ∪ B ∪ C
```

### Difference

Subtracts subsequent shapes from the first.

```
result = A − B − C
```

!!! tip
    Use Difference to cut holes in a surrounding domain — essential for multi-domain problems such as a conductor embedded in a dielectric.

### Intersection

Retains only the region common to all input shapes.

```
result = A ∩ B
```

---

## Boundary Tagging

After each primitive or boolean operation, Elementa automatically creates named physical groups for all resulting boundaries. These names appear in the boundary condition assignment panel and the gmsh `.msh` file.

| Primitive | Boundary names |
|-----------|---------------|
| Rectangle | `<name>_edge_0` … `_edge_3` |
| Disk | `<name>_edge_0` |
| Box | `<name>_face_0` … `_face_5` |
| Boolean result | `<name>_bnd_0`, `<name>_bnd_1`, … |
