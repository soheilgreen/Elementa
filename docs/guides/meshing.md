# Meshing

Elementa delegates mesh generation entirely to the [gmsh](https://gmsh.info/) library, which provides robust triangular (2-D) and tetrahedral (3-D) meshing.

---

## Generating a Mesh

1. Build your geometry in the **Geometry** panel.
2. Open the **Mesh** panel.
3. Set the **Element Size** (in metres).
4. Click **Generate Mesh**.

The mesh is displayed on the canvas. Boundaries are colour-coded and labelled.

---

## Element Size

The **Element Size** parameter sets a uniform target for the maximum edge length of mesh elements. Smaller values produce finer meshes with more elements:

| Element Size | Quality | Solve Time |
|-------------|---------|-----------|
| Large (e.g. 0.1) | Coarse — fast | Seconds |
| Medium (e.g. 0.02) | Moderate | Seconds–minutes |
| Small (e.g. 0.005) | Fine — accurate | Minutes |

!!! tip
    Start with a coarse mesh to verify boundary conditions and geometry, then refine before production runs.

---

## Mesh Quality

gmsh uses the Delaunay algorithm for 2-D and a combination of Delaunay and Frontal algorithms for 3-D. The resulting meshes are:

- **Conformal** — elements share complete edges/faces at boundaries
- **Well-graded** — smooth transition between regions
- **Compatible with scikit-fem** — the `.msh` (v2.2) format is read directly by `skfem.Mesh.load()`

---

## Mesh File

The generated mesh is stored as a gmsh `.msh` (version 2.2) file in a temporary directory during the session. When you **Save** the project, the mesh is embedded in the `.elem` archive alongside the model state and results.

---

## Element Types

| Dimension | Element | scikit-fem type |
|-----------|---------|----------------|
| 2-D | Linear triangle (P1) | `ElementTriP1` |
| 3-D | Linear tetrahedron (P1) | `ElementTetP1` |

P1 elements use linear shape functions — one degree of freedom per node. This is the standard choice for the Laplace/Poisson and heat equations solved by Elementa.

---

## Physical Groups and Boundaries

After mesh generation, gmsh assigns **physical group names** to all domains and boundaries based on the names you specified in the Geometry panel. These names are used in the Physics panel to assign boundary conditions and in the solver to locate degrees of freedom.

You can inspect boundary names in the Model Builder tree or by clicking boundaries on the canvas.
