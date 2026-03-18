from typing import Dict, Type

class ShapeDef:
    kind: str = ""
    dim: int = 0
    params: Dict[str, str] = {}
    
    @classmethod
    def build(cls, cad, name: str, params: Dict[str, float]) -> int:
        """Returns the gmsh tag of the built object."""
        raise NotImplementedError()

class RectangleDef(ShapeDef):
    kind = "rectangle"
    dim = 2
    params = {"dx": "1.0", "dy": "1.0", "cx": "0.0", "cy": "0.0"}
    
    @classmethod
    def build(cls, cad, name, params):
        return cad.add_rectangle(name, params['dx'], params['dy'], (params['cx'], params['cy']))

class DiskDef(ShapeDef):
    kind = "disk"
    dim = 2
    params = {"rx": "0.5", "ry": "0.5", "cx": "0.0", "cy": "0.0"}
    
    @classmethod
    def build(cls, cad, name, params):
        return cad.add_disk(name, params['rx'], params['ry'], (params['cx'], params['cy']))

class PolygonDef(ShapeDef):
    kind = "polygon"
    dim = 2
    params = {"points": "[(0,0), (1,0), (0.5,0.8)]"}
    
    @classmethod
    def build(cls, cad, name, params):
        return cad.add_polygon(name, params['points'])

class BoxDef(ShapeDef):
    kind = "box"
    dim = 3
    params = {"dx": "1.0", "dy": "1.0", "dz": "1.0", "cx": "0.0", "cy": "0.0", "cz": "0.0"}
    
    @classmethod
    def build(cls, cad, name, params):
        return cad.add_box(name, params['dx'], params['dy'], params['dz'], (params['cx'], params['cy'], params['cz']))

class SphereDef(ShapeDef):
    kind = "sphere"
    dim = 3
    params = {"r": "0.5", "cx": "0.0", "cy": "0.0", "cz": "0.0"}
    
    @classmethod
    def build(cls, cad, name, params):
        return cad.add_sphere(name, params['r'], (params['cx'], params['cy'], params['cz']))

class CylinderDef(ShapeDef):
    kind = "cylinder"
    dim = 3
    params = {"r": "0.2", "h": "1.0", "cx": "0.0", "cy": "0.0", "cz": "0.0"}
    
    @classmethod
    def build(cls, cad, name, params):
        return cad.add_cylinder(name, params['r'], params['h'], (params['cx'], params['cy'], params['cz']))

SHAPE_REGISTRY: Dict[str, Type[ShapeDef]] = {
    cls.kind: cls for cls in [RectangleDef, DiskDef, PolygonDef, BoxDef, SphereDef, CylinderDef]
}
