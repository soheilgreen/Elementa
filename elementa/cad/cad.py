"""
Programmatic CAD + meshing utility using gmsh Python API only.
Supports both 2D (triangular surface meshes) and 3D (tetrahedral volume meshes).

Dependencies:
    pip install gmsh meshio numpy
"""

import gmsh

from ..core.logger import get_logger

logger = get_logger(__name__)

class ElementaCAD:
    def __init__(self, verbose=True):
        self.verbose = verbose
        if not gmsh.isInitialized():
            gmsh.initialize()
        gmsh.model.add("elementa_cad")

    def _log(self, *args):
        if self.verbose:
            logger.info(" ".join(map(str, args)))

    # -----------------------
    # 2D Primitives
    # -----------------------
    def add_rectangle(self, name, dx, dy, center=(0, 0), tag_boundaries=True):
        cx, cy = center
        x0, y0 = cx - dx / 2, cy - dy / 2
        surf = gmsh.model.occ.addRectangle(x0, y0, 0, dx, dy)
        gmsh.model.occ.synchronize()
        if name:
            gmsh.model.addPhysicalGroup(2, [surf], name=name)
            if tag_boundaries:
                edges = gmsh.model.getBoundary([(2, surf)], oriented=True)
                for i, eid in enumerate(edges):
                    gmsh.model.addPhysicalGroup(1, [eid[1]], name=f"{name}_edge_{i}")
        return surf

    def add_disk(self, name, rx, ry=None, center=(0, 0), tag_boundary=True):
        if ry is None:
            ry = rx
        cx, cy = center
        surf = gmsh.model.occ.addDisk(cx, cy, 0, rx, ry)
        gmsh.model.occ.synchronize()
        if name:
            gmsh.model.addPhysicalGroup(2, [surf], name=name)
            if tag_boundary:
                edges = gmsh.model.getBoundary([(2, surf)], oriented=False)
                for i, eid in enumerate(edges):
                    gmsh.model.addPhysicalGroup(1, [eid[1]], name=f"{name}_edge_{i}")
        return surf

    def add_polygon(self, name, points, tag_boundary=True):
        pt_tags = [gmsh.model.occ.addPoint(px, py, 0) for px, py in points]
        lines = [gmsh.model.occ.addLine(pt_tags[i-1], pt_tags[i]) for i in range(len(pt_tags))]
        wire = gmsh.model.occ.addWire(lines)
        surf = gmsh.model.occ.addPlaneSurface([wire])
        gmsh.model.occ.synchronize()
        if name:
            gmsh.model.addPhysicalGroup(2, [surf], name=name)
            if tag_boundary:
                edges = gmsh.model.getBoundary([(2, surf)], oriented=False)
                for i, eid in enumerate(edges):
                    gmsh.model.addPhysicalGroup(1, [eid[1]], name=f"{name}_edge_{i}")
        return surf

    # -----------------------
    # 3D Primitives
    # -----------------------
    def add_box(self, name, dx, dy, dz, center=(0, 0, 0), tag_boundaries=True):
        cx, cy, cz = center
        x0, y0, z0 = cx - dx / 2, cy - dy / 2, cz - dz / 2
        vol = gmsh.model.occ.addBox(x0, y0, z0, dx, dy, dz)
        gmsh.model.occ.synchronize()
        if name:
            gmsh.model.addPhysicalGroup(3, [vol], name=name)
            if tag_boundaries:
                faces = gmsh.model.getBoundary([(3, vol)], oriented=True)
                for i, fid in enumerate(faces):
                    gmsh.model.addPhysicalGroup(2, [fid[1]], name=f"{name}_face_{i}")
        return vol

    def add_sphere(self, name, r, center=(0, 0, 0), tag_boundary=True):
        cx, cy, cz = center
        vol = gmsh.model.occ.addSphere(cx, cy, cz, r)
        gmsh.model.occ.synchronize()
        if name:
            gmsh.model.addPhysicalGroup(3, [vol], name=name)
            if tag_boundary:
                faces = gmsh.model.getBoundary([(3, vol)], oriented=False)
                for i, fid in enumerate(faces):
                    gmsh.model.addPhysicalGroup(2, [fid[1]], name=f"{name}_face_{i}")
        return vol

    def add_cylinder(self, name, r, h, base_center=(0, 0, 0), axis=(0, 0, 1), tag_boundary=True):
        bx, by, bz = base_center
        ax, ay, az = axis
        vol = gmsh.model.occ.addCylinder(bx, by, bz, h * ax, h * ay, h * az, r)
        gmsh.model.occ.synchronize()
        if name:
            gmsh.model.addPhysicalGroup(3, [vol], name=name)
            if tag_boundary:
                faces = gmsh.model.getBoundary([(3, vol)], oriented=False)
                for i, fid in enumerate(faces):
                    gmsh.model.addPhysicalGroup(2, [fid[1]], name=f"{name}_face_{i}")
        return vol

    # -----------------------
    # Boolean operations
    # -----------------------
    def boolean_union(self, entities, dim, name="union"):
        if len(entities) < 2:
            return [entities[0][1]]
        
        main_object = [entities[0]]
        tool_objects = entities[1:]
        
        out, _ = gmsh.model.occ.fuse(main_object, tool_objects, removeTool=True)
        gmsh.model.occ.synchronize()
        
        ids = [v[1] for v in out]
        if name and ids:
            gmsh.model.addPhysicalGroup(dim, ids, name=name)
            boundaries = gmsh.model.getBoundary(out, combined=True, oriented=False, recursive=False)
            for i, b in enumerate(boundaries):
                gmsh.model.addPhysicalGroup(dim - 1, [b[1]], name=f"{name}_bnd_{i}")
        return ids

    def boolean_difference(self, objectA, subtracts, dim, name="diff"):
        out, _ = gmsh.model.occ.cut(objectA, subtracts, removeTool=True)
        gmsh.model.occ.synchronize()
        ids = [v[1] for v in out]
        if name and ids:
            gmsh.model.addPhysicalGroup(dim, ids, name=name)
            boundaries = gmsh.model.getBoundary(out, combined=True, oriented=False, recursive=False)
            for i, b in enumerate(boundaries):
                gmsh.model.addPhysicalGroup(dim - 1, [b[1]], name=f"{name}_bnd_{i}")
        return ids

    def boolean_intersection(self, objs, dim, name="intersect"):
        if len(objs) < 2:
            return [objs[0][1]]
        
        main_object = [objs[0]]
        tool_objects = objs[1:]

        out, _ = gmsh.model.occ.intersect(main_object, tool_objects, removeObject=True, removeTool=True)
        gmsh.model.occ.synchronize()
        
        ids = [v[1] for v in out]
        if name and ids:
            gmsh.model.addPhysicalGroup(dim, ids, name=name)
            boundaries = gmsh.model.getBoundary(out, combined=True, oriented=False, recursive=False)
            for i, b in enumerate(boundaries):
                gmsh.model.addPhysicalGroup(dim - 1, [b[1]], name=f"{name}_bnd_{i}")
        return ids

    # -----------------------
    # Meshing & export
    # -----------------------
    def generate_mesh(self, dim=2, mesh_size=None):
        gmsh.model.occ.synchronize()
        if mesh_size is not None:
            gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
        gmsh.model.mesh.generate(dim)

    def export(self, basename="elementa_cad_output"):
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        mshfile = f"{basename}.msh"
        gmsh.write(mshfile)
        self._log("Wrote", mshfile)

    def finalize(self):
        if gmsh.isInitialized():
            gmsh.finalize()

