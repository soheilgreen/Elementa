# Adding a Geometry Primitive

This guide shows how to add a new primitive shape to Elementa.

---

## 1. Add the Build Method to ElementaCAD

Open `elementa/cad/cad.py` and add a new method to `ElementaCAD`. For example, a torus:

```python
def add_torus(self, name: str, R: float, r: float,
              center=(0, 0, 0), tag_boundary=True) -> int:
    """
    Add a torus.

    Args:
        name:   Physical group name.
        R:      Major radius (centre to tube centre).
        r:      Minor radius (tube radius).
        center: Centre coordinates (cx, cy, cz).

    Returns:
        gmsh volume tag.
    """
    cx, cy, cz = center
    vol = gmsh.model.occ.addTorus(cx, cy, cz, R, r)
    gmsh.model.occ.synchronize()
    if name:
        gmsh.model.addPhysicalGroup(3, [vol], name=name)
        if tag_boundary:
            faces = gmsh.model.getBoundary([(3, vol)], oriented=False)
            for i, fid in enumerate(faces):
                gmsh.model.addPhysicalGroup(2, [fid[1]], name=f"{name}_face_{i}")
    return vol
```

---

## 2. Add a ShapeDef to the Registry

Open `elementa/core/geometry_registry.py` and add:

```python
class TorusDef(ShapeDef):
    kind = "torus"
    dim = 3
    params = {"R": "0.5", "r": "0.2", "cx": "0.0", "cy": "0.0", "cz": "0.0"}

    @classmethod
    def build(cls, cad, name, params):
        return cad.add_torus(
            name, params["R"], params["r"],
            center=(params["cx"], params["cy"], params["cz"]),
        )
```

Then add it to `SHAPE_REGISTRY`:

```python
SHAPE_REGISTRY: Dict[str, Type[ShapeDef]] = {
    cls.kind: cls for cls in [
        RectangleDef, DiskDef, PolygonDef,
        BoxDef, SphereDef, CylinderDef,
        TorusDef,        # ← new
    ]
}
```

---

## 3. Add a UI Button

In `elementa/ui/ribbon_toolbar.py`, add a button to the Geometry tab that calls an `add_torus` handler. The handler should create a `GeometryItem(kind="torus", name=..., params={...})` and call `project.add_geometry_item(item)`.

---

## 4. Add an Icon

Add a 350×350 PNG named `torus.png` to `elementa/assets/` and reference it in the ribbon button.

---

## Checklist

- [ ] `ElementaCAD.add_<shape>` method added with gmsh OCC call
- [ ] `ShapeDef` subclass added with correct `kind`, `dim`, `params`
- [ ] `ShapeDef.build()` implemented calling the new `ElementaCAD` method
- [ ] Class added to `SHAPE_REGISTRY`
- [ ] (Optional) Ribbon button and icon added
