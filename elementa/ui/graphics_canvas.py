import numpy as np
import gmsh
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

class InteractiveCanvas(FigureCanvas):
    boundarySelected = pyqtSignal(str, bool)
    domainSelected = pyqtSignal(str, bool)
    pointProbed = pyqtSignal(tuple)

    def __init__(self, owner, parent=None):
        self.fig = Figure(figsize=(8, 6), tight_layout=True)
        super().__init__(self.fig)
        self.owner = owner
        self.ax = None
        self._is_3d = False
        self._mesh = None
        self._selected_boundaries = set()
        self._selected_domains = set()
        self._boundary_patches = {}
        self._domain_patches = {}
        self._probe_artists = []
        self._pan_start_pos = None
        self._click_pos = None
        self._picked_artist = None
        self.mpl_connect('pick_event', self._on_pick)
        self.mpl_connect('button_press_event', self._on_mouse_press)
        self.mpl_connect('button_release_event', self._on_mouse_release)
        self.mpl_connect('motion_notify_event', self._on_mouse_move)
        self.mpl_connect('scroll_event', self._on_scroll)

    def clear(self):
        self.fig.clear(); self.ax = None; self._is_3d = False
        self._selected_boundaries.clear()
        self._selected_domains.clear()
        self._boundary_patches.clear()
        self._domain_patches.clear()
        self.draw_idle()

    def _prepare_ax(self, is_3d=False):
        if self.ax and self.ax in self.fig.axes and self._is_3d == is_3d:
            self.ax.clear()
        else:
            self.fig.clear(); self._is_3d = is_3d
            self.ax = self.fig.add_subplot(111, projection='3d' if is_3d else None)
        return self.ax

    def show_geometry(self, gmsh_instance, dim):
        self.fig.clear()
        ax = self._prepare_ax(is_3d=(dim == 3))
        gmsh_instance.model.occ.synchronize(); gmsh.model.mesh.generate(1)
        nodes, coords, _ = gmsh.model.mesh.getNodes(includeBoundary=True)
        coords = coords.reshape(-1, 3)
        if not coords.size: self.owner.log("No geometry nodes to display."); return
        element_types, _, node_tags = gmsh_instance.model.mesh.getElements(1)
        if not element_types: self.owner.log("No 1D elements for visualization."); return
        line_nodes = node_tags[0].reshape(-1, 2)
        node_map = {tag: i for i, tag in enumerate(nodes)}
        if dim == 2:
            for n1_tag, n2_tag in line_nodes:
                p1 = coords[node_map[n1_tag]]; p2 = coords[node_map[n2_tag]]
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'k-')
            ax.set_aspect('equal', 'box')
        else:
            for n1_tag, n2_tag in line_nodes:
                p1 = coords[node_map[n1_tag]]; p2 = coords[node_map[n2_tag]]
                ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], 'k-')
        ax.set_title("Geometry Preview"); self.draw_idle(); gmsh.model.mesh.clear()

    def show_mesh(self, mesh):
        # More aggressive figure clearing
        self.fig.clf()  # Clear figure completely
        self._mesh = mesh; is_3d = mesh.dim() == 3; ax = self._prepare_ax(is_3d)
        
        self._boundary_patches.clear()
        
        if is_3d:
            bnd_facets = mesh.facets[:, mesh.boundary_facets()]
            # Plot the transparent outline of all boundaries first
            ax.plot_trisurf(mesh.p[0,:], mesh.p[1,:], mesh.p[2,:], triangles=bnd_facets.T,
                            color='lightblue', alpha=0.1, edgecolor='none')
                            
            # Highlight Subdomains (Domains) in 3D
            if hasattr(mesh, 'subdomains') and mesh.subdomains:
                for name, elem_indices in mesh.subdomains.items():
                    if name in self._selected_domains:
                        faces = []
                        for idx in elem_indices:
                            n1, n2, n3, n4 = mesh.t[:, idx]
                            faces.extend([[n1, n2, n3], [n1, n2, n4], [n1, n3, n4], [n2, n3, n4]])
                        if faces:
                            import numpy as np
                            ax.plot_trisurf(mesh.p[0,:], mesh.p[1,:], mesh.p[2,:], triangles=np.array(faces),
                                            color='red', alpha=0.3, edgecolor='none')
            
            for name, fac_idx in mesh.boundaries.items():
                try:
                    # In skfem, mesh.boundaries provides arrays of facet indices
                    f_nodes = mesh.facets[:, fac_idx]
                except Exception as e:
                    continue
                color = 'red' if name in self._selected_boundaries else 'lightblue'
                alpha = 0.8 if name in self._selected_boundaries else 0.5
                linewidth = 1.0 if name in self._selected_boundaries else 0.2
                surf = ax.plot_trisurf(mesh.p[0,:], mesh.p[1,:], mesh.p[2,:], triangles=f_nodes.T,
                                       color=color, alpha=alpha, edgecolor='k', linewidth=linewidth)
                surf.set_picker(True) # Ensure picker is enabled for Poly3DCollection
                self._boundary_patches[surf] = name
        else:
            ax.triplot(mesh.p[0, :], mesh.p[1, :], mesh.t.T, linewidth=0.5, color='k', zorder=1)
            
            # Highlight Subdomains (Domains)
            if hasattr(mesh, 'subdomains') and mesh.subdomains:
                from matplotlib.patches import Polygon
                from matplotlib.collections import PatchCollection
                
                polygons = []
                for name, elem_indices in mesh.subdomains.items():
                    if name in self._selected_domains:
                        for idx in elem_indices:
                            pts = mesh.p[:, mesh.t[:, idx]].T  # (3, 2)
                            polygons.append(Polygon(pts))
                            
                if polygons:
                    p = PatchCollection(polygons, facecolor='red', alpha=0.5, edgecolor='none', zorder=2)
                    ax.add_collection(p)
            
            # Highlight Boundaries
            for name, fac_idx in mesh.boundaries.items():
                try:
                    # In skfem, mesh.boundaries provides arrays of facet indices
                    f_nodes = mesh.facets[:, fac_idx]
                except Exception:
                    continue
                    
                color = 'red' if name in self._selected_boundaries else 'blue'
                linewidth = 6.0 if name in self._selected_boundaries else 2.0
                
                # Plot each segment of the boundary
                for i in range(f_nodes.shape[1]):
                    n1, n2 = f_nodes[:, i]
                    p1 = mesh.p[:, n1]
                    p2 = mesh.p[:, n2]
                    line, = ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, linewidth=linewidth, picker=5, zorder=10)
                    self._boundary_patches[line] = name
            ax.set_aspect('equal', 'box')
        ax.set_title("Mesh")
        # Force multiple levels of refresh
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def set_selected_boundaries(self, names):
        self._selected_boundaries = names
        if self._mesh:
            self.show_mesh(self._mesh)

    def set_selected_domains(self, names):
        self._selected_domains = set(names)
        if self._mesh:
            self.show_mesh(self._mesh)

    def plot_results(self, spec, mesh, basis, result_data, field_type, unit=''):
        # Clear figure to remove old colorbars and plots
        self.fig.clear()
        
        is_3d = mesh.dim() == 3
        ax = self._prepare_ax(is_3d)
        
        alpha = spec.get('opacity', 1.0)
        show_edges = spec.get('show_edges', False)
        
        if spec['type'] == "Surface":
            cmap = spec.get('cmap', 'viridis')
            label = spec.get('expr', '')

            # Auto-detect: scalar → plot directly, vector → compute norm
            if field_type == "vector" and result_data is not None:
                if is_3d:
                    data = np.sqrt(result_data[0]**2 + result_data[1]**2 + result_data[2]**2)
                else:
                    data = np.sqrt(result_data[0]**2 + result_data[1]**2)
                if unit:
                    label = f"{label} [{unit}]"
            elif field_type == "scalar" and result_data is not None:
                data = result_data
                if unit:
                    label = f"{label} [{unit}]"
            else:
                return  # No data to plot

            if is_3d:
                bnd_facets = mesh.facets[:, mesh.boundary_facets()]
                edge_color = 'k' if show_edges else 'none'
                line_width = 0.2 if show_edges else 0
                surf = ax.plot_trisurf(mesh.p[0,:], mesh.p[1,:], mesh.p[2,:], triangles=bnd_facets.T, cmap=cmap, shade=False, alpha=alpha, edgecolor=edge_color, linewidth=line_width)
                
                colors = np.mean(data[bnd_facets], axis=0)
                surf.set_array(colors)
                # Compute and set the explicit color limits so the colorbar scales correctly
                if 'clim' in spec:
                    vmin, vmax = spec['clim']
                else:
                    vmin, vmax = colors.min(), colors.max()
                
                if vmax - vmin < 1e-10:
                    vmin, vmax = vmin - 0.05, vmax + 0.05
                surf.set_clim(vmin, vmax)
                
                self.fig.colorbar(surf, ax=ax, label=label)
            else:
                tpc = ax.tripcolor(mesh.p[0,:], mesh.p[1,:], mesh.t.T, data, shading='gouraud', cmap=cmap, alpha=alpha)
                if show_edges:
                    ax.triplot(mesh.p[0,:], mesh.p[1,:], mesh.t.T, color='k', linewidth=0.5, alpha=alpha)
                if 'clim' in spec:
                    vmin, vmax = spec['clim']
                else:
                    vmin, vmax = data.min(), data.max()
                    
                if vmax - vmin < 1e-10:
                    vmin, vmax = vmin - 0.05, vmax + 0.05
                tpc.set_clim(vmin, vmax)
                self.fig.colorbar(tpc, ax=ax, label=label)
        elif spec['type'] == "Arrow":
            # Arrow plots only work with vector data
            if field_type != "vector" or result_data is None:
                return
            if is_3d:
                Ex, Ey, Ez = result_data
                skip = max(1, len(Ex) // 100)
                box_size = np.max(np.ptp(mesh.p, axis=1)) if mesh.p.size > 0 else 1.0
                ax.quiver(mesh.p[0, ::skip], mesh.p[1, ::skip], mesh.p[2, ::skip],
                          Ex[::skip], Ey[::skip], Ez[::skip], color='black', normalize=True, length=0.1*box_size)
            else:
                Ex, Ey = result_data
                skip = max(1, len(Ex) // 100)
                ax.quiver(mesh.p[0, ::skip], mesh.p[1, ::skip],
                          Ex[::skip], Ey[::skip], color='black')
        ax.set_title(spec['name'])
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
    def draw_probe(self, spec: dict):
        """Draw a probe indicator overlay on the current axes."""
        if not self.ax: return
        
        # Clear previous probe markers
        for artist in self._probe_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self._probe_artists.clear()
        
        if spec['type'] == 'Point Probe':
            x, y = spec.get('coord_x', 0.0), spec.get('coord_y', 0.0)
            if self._is_3d:
                z = spec.get('coord_z', 0.0)
                artist, = self.ax.plot([x], [y], [z], 'ro', markersize=8, markeredgecolor='white')
            else:
                artist, = self.ax.plot(x, y, 'ro', markersize=8, markeredgecolor='white')
            self._probe_artists.append(artist)
            
        elif spec['type'] == 'Line Probe':
            x0, y0 = spec.get('start_x', 0.0), spec.get('start_y', 0.0)
            x1, y1 = spec.get('end_x', 1.0), spec.get('end_y', 1.0)
            if self._is_3d:
                z0, z1 = spec.get('start_z', 0.0), spec.get('end_z', 1.0)
                artist, = self.ax.plot([x0, x1], [y0, y1], [z0, z1], 'r-', linewidth=3)
            else:
                artist, = self.ax.plot([x0, x1], [y0, y1], 'r-', linewidth=3)
            self._probe_artists.append(artist)
            
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
    def _on_pick(self, event):
        if event.artist in self._boundary_patches:
            self._picked_artist = event.artist

    def _on_mouse_press(self, event):
        if event.inaxes != self.ax: return
        if event.button == 3: self._pan_start_pos = (event.xdata, event.ydata)
        if event.button == 1: self._click_pos = (event.x, event.y)

    def _on_mouse_release(self, event):
        if event.inaxes == self.ax and event.button == 1 and self._click_pos:
            dx = event.x - self._click_pos[0]
            dy = event.y - self._click_pos[1]
            if (dx*dx + dy*dy) < 25:
                # Get context
                ctx = getattr(self.owner.project, 'active_panel_context', "")
                is_ctrl = getattr(event, 'key', None) == 'control'
                
                # Context-aware picking
                if ctx.startswith("bc_"):
                    if self._picked_artist:
                        name = self._boundary_patches.get(self._picked_artist)
                        if name:
                            self.boundarySelected.emit(name, is_ctrl)
                elif ctx.startswith("mat_") or ctx.startswith("physfeat_"):
                    # Domain picking (Using projected display pixels for 2D/3D robust picking)
                    if self._mesh and hasattr(self._mesh, 'subdomains') and event.x is not None and event.y is not None:
                        centroids = self._mesh.p[:, self._mesh.t].mean(axis=1) # (dim, Ne)
                        
                        if self._is_3d:
                            from mpl_toolkits.mplot3d import proj3d
                            x2, y2, _ = proj3d.proj_transform(centroids[0], centroids[1], centroids[2], self.ax.get_proj())
                            display_coords = self.ax.transData.transform(np.column_stack([x2, y2]))
                        else:
                            display_coords = self.ax.transData.transform(centroids.T)
                            
                        dist_sq = (display_coords[:, 0] - event.x)**2 + (display_coords[:, 1] - event.y)**2
                        closest_elem = np.argmin(dist_sq)
                        
                        for dom_name, elems in self._mesh.subdomains.items():
                            if closest_elem in elems:
                                self.domainSelected.emit(dom_name, is_ctrl)
                                break
                                
        self._pan_start_pos = None
        self._click_pos = None
        self._picked_artist = None

    def _on_mouse_move(self, event):
        if event.inaxes != self.ax: return
        if self._pan_start_pos and not self._is_3d:
            x_start, y_start = self._pan_start_pos
            if event.xdata is None or event.ydata is None: return
            dx = event.xdata - x_start; dy = event.ydata - y_start
            cur_xlim = self.ax.get_xlim(); cur_ylim = self.ax.get_ylim()
            self.ax.set_xlim([cur_xlim[0] - dx, cur_xlim[1] - dx])
            self.ax.set_ylim([cur_ylim[0] - dy, cur_ylim[1] - dy]); self.draw_idle()
    
    def _on_scroll(self, event):
        if event.inaxes != self.ax: return
        base_scale = 1.1; cur_xlim = self.ax.get_xlim(); cur_ylim = self.ax.get_ylim()
        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None: return
        scale_factor = 1 / base_scale if event.button == 'up' else base_scale
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        rel_x = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rel_y = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        self.ax.set_xlim([xdata - new_width * (1 - rel_x), xdata + new_width * rel_x])
        self.ax.set_ylim([ydata - new_height * (1 - rel_y), ydata + new_height * rel_y])
        self.draw_idle()

