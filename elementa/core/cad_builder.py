import gmsh
from typing import Dict, Optional

from ..cad.cad import ElementaCAD
from .project_state import ProjectState
from .evaluator import ParameterEvaluator
from .geometry_registry import SHAPE_REGISTRY
from .exceptions import GeometryBuildError
from .logger import get_logger

logger = get_logger(__name__)

class CADBuilder:
    @staticmethod
    def build_model(project: ProjectState) -> Optional[ElementaCAD]:
        """Builds the CAD model from the project state, returning the ElementaCAD instance on success."""
        if not gmsh.isInitialized():
            gmsh.initialize()
        gmsh.clear()
            
        cad = ElementaCAD(verbose=False)
        tags_map: Dict[str, tuple[int, int]] = {}
        
        try:
            eval_params = ParameterEvaluator.resolve_parameters(project.parameters)
        except Exception as e:
            logger.error(f"Failed to evaluate parameters before CAD build: {e}")
            raise GeometryBuildError(f"Parameter evaluation failed: {e}") from e

        consumed_primitives = set()
        for bo in project.boolean_operations:
            for input_name in bo.inputs:
                if any(gi.name == input_name for gi in project.geometry_items):
                    consumed_primitives.add(input_name)

        # Build Primitives
        for gi in project.geometry_items:
            try:
                primitive_name = gi.name if gi.name not in consumed_primitives else ""
                
                if gi.kind not in SHAPE_REGISTRY:
                    raise GeometryBuildError(f"Unknown geometry kind: {gi.kind}")
                
                shape_cls = SHAPE_REGISTRY[gi.kind]
                
                evaluated_shape_params = {}
                for k, v in gi.params.items():
                    if k == 'points':
                        evaluated_shape_params[k] = ParameterEvaluator.evaluate_points(str(v), eval_params)
                    else:
                        evaluated_shape_params[k] = ParameterEvaluator.evaluate_expression(str(v), eval_params)
                
                tag = shape_cls.build(cad, primitive_name, evaluated_shape_params)
                tags_map[gi.name] = (shape_cls.dim, tag)
                
            except Exception as e:
                msg = f"Failed to create primitive '{gi.name}': {e}"
                logger.error(msg)
                if gmsh.isInitialized(): gmsh.clear()
                raise GeometryBuildError(msg) from e
        
        # Build Boolean Operations
        for bo in project.boolean_operations:
            try:
                if not all(name in tags_map for name in bo.inputs):
                    raise ValueError(f"One or more inputs for '{bo.name}' not found: {bo.inputs}")

                input_tags = [tags_map[name] for name in bo.inputs]
                dim = project.space_dim
                new_tags = []

                if bo.kind == "union":
                    new_tags = cad.boolean_union(input_tags, dim, name=bo.name)
                elif bo.kind == "difference":
                    if len(input_tags) < 2: raise ValueError("Difference needs >= 2 inputs.")
                    objectA = [input_tags[0]]
                    subtracts = input_tags[1:]
                    new_tags = cad.boolean_difference(objectA, subtracts, dim, name=bo.name)
                elif bo.kind == "intersection":
                    if len(input_tags) < 2: raise ValueError("Intersection needs >= 2 inputs.")
                    new_tags = cad.boolean_intersection(input_tags, dim, name=bo.name)
                
                if new_tags:
                    tags_map[bo.name] = (dim, new_tags[0])
                else:
                    logger.warning(f"Boolean operation '{bo.name}' produced no output entities.")

            except Exception as e:
                msg = f"Failed to perform boolean op '{bo.name}': {e}"
                logger.error(msg)
                if gmsh.isInitialized(): gmsh.clear()
                raise GeometryBuildError(msg) from e
                
        return cad
