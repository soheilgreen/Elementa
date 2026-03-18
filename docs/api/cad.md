# elementa.cad — API Reference

## `ElementaCAD`

High-level wrapper around the gmsh OpenCASCADE kernel. Manages geometry creation, boolean operations, meshing, and export.

```python
from elementa.cad import ElementaCAD

cad = ElementaCAD(verbose=False)
```

### Constructor

```python
ElementaCAD(verbose: bool = True)
```

Initialises gmsh if not already initialised, and adds a new gmsh model.

---

### 2-D Primitives

#### `add_rectangle`

```python
def add_rectangle(
    name: str,
    dx: float,
    dy: float,
    center: Tuple[float, float] = (0, 0),
    tag_boundaries: bool = True,
) -> int
```

Creates a rectangle centred at `center` with width `dx` and height `dy`.  
Returns the gmsh surface tag.  
Boundary physical groups: `<name>_edge_0` … `<name>_edge_3`.

#### `add_disk`

```python
def add_disk(
    name: str,
    rx: float,
    ry: float = None,
    center: Tuple[float, float] = (0, 0),
    tag_boundary: bool = True,
) -> int
```

Creates an elliptical disk. If `ry` is omitted, a circle of radius `rx` is created.

#### `add_polygon`

```python
def add_polygon(
    name: str,
    points: List[Tuple[float, float]],
    tag_boundary: bool = True,
) -> int
```

Creates a planar polygon from a list of `(x, y)` vertices.

---

### 3-D Primitives

#### `add_box`

```python
def add_box(
    name: str,
    dx: float, dy: float, dz: float,
    center: Tuple[float, float, float] = (0, 0, 0),
    tag_boundaries: bool = True,
) -> int
```

#### `add_sphere`

```python
def add_sphere(
    name: str,
    r: float,
    center: Tuple[float, float, float] = (0, 0, 0),
    tag_boundary: bool = True,
) -> int
```

#### `add_cylinder`

```python
def add_cylinder(
    name: str,
    r: float,
    h: float,
    base_center: Tuple[float, float, float] = (0, 0, 0),
    axis: Tuple[float, float, float] = (0, 0, 1),
    tag_boundary: bool = True,
) -> int
```

---

### Boolean Operations

All boolean methods return a list of resulting entity tags and create named physical groups for the result domain and its boundaries.

#### `boolean_union`

```python
def boolean_union(
    entities: List[Tuple[int, int]],
    dim: int,
    name: str = "union",
) -> List[int]
```

#### `boolean_difference`

```python
def boolean_difference(
    objectA: List[Tuple[int, int]],
    subtracts: List[Tuple[int, int]],
    dim: int,
    name: str = "diff",
) -> List[int]
```

#### `boolean_intersection`

```python
def boolean_intersection(
    objs: List[Tuple[int, int]],
    dim: int,
    name: str = "intersect",
) -> List[int]
```

---

### Meshing & Export

#### `generate_mesh`

```python
def generate_mesh(dim: int = 2, mesh_size: float = None) -> None
```

Runs gmsh mesh generation. Set `mesh_size` to override the global element size.

#### `export`

```python
def export(basename: str = "elementa_cad_output") -> None
```

Writes a `.msh` file (gmsh version 2.2 format).

#### `finalize`

```python
def finalize() -> None
```

Finalises and frees gmsh resources.
