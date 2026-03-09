"""
LPSolverEngine - Week-4 Execution Layer

Implements:
DSL → AST → Canonical → Matrix → Solver → Result

Features:
1. Solver integration with SciPy linprog
2. Result mapping with variable names
3. Usefulness range computation (for paving-type models)
4. Error handling (infeasible, unbounded, numerical)
5. Deterministic execution
"""

import math
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass

# Import existing solver
try:
    from formula.lp_solver import LPSolver
except ImportError:
    from lp_solver import LPSolver


@dataclass
class LPSolution:
    """Structured LP solution result."""
    status: str  # "optimal", "infeasible", "unbounded", "failed"
    objective: Optional[float]
    solution: Dict[str, float]  # variable_name -> value
    usefulness_range: Optional[Dict[str, Tuple[float, float]]]  # variable_name -> (low, high)
    solver_info: Dict[str, Any]
    variables: List[str]  # Original variable order


class LPSolverEngine:
    """
    Week-4 Execution Layer for LP DSL Engine.
    
    Converts matrices from MatrixBuilderV3 to structured results.
    """
    
    def __init__(self, method: str = "highs", tolerance: float = 1e-9):
        """
        Initialize solver engine.
        
        Args:
            method: Solver method for linprog
            tolerance: Numerical tolerance for floating cleanup
        """
        self.solver = LPSolver(method=method)
        self.tolerance = tolerance
    
    def solve_lp(self, matrices: Dict[str, Any], objective_type: str = "minimize") -> Dict[str, Any]:
        """
        Solve LP problem from matrices (STEP-1).
        
        Args:
            matrices: Dictionary from MatrixBuilderV3 containing:
                - c: Objective coefficients
                - A_ub: Inequality constraint matrix
                - b_ub: Inequality constraint vector
                - bounds: Variable bounds
                - variables: Variable names in order
            objective_type: "minimize" or "maximize"
                
        Returns:
            Raw solver result dictionary
        """
        # Extract matrices
        c = matrices['c']
        A_ub = matrices.get('A_ub')
        b_ub = matrices.get('b_ub')
        bounds = matrices.get('bounds')
        
        # Determine if we're maximizing or minimizing (STEP-2)
        maximize = (objective_type.lower() == "maximize")
        
        # Solve using LPSolver
        result = self.solver.solve(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            bounds=bounds,
            maximize=maximize
        )
        
        return result
    
    def _cleanup_float(self, value: Optional[float]) -> Optional[float]:
        """
        Zero out near-zero floating point values.
        
        if abs(value) < tolerance: value = 0.0
        """
        if value is None:
            return None
        return 0.0 if abs(value) < self.tolerance else float(value)
    
    def _cleanup_float_value(self, value: float) -> float:
        """
        Zero out near-zero floating point values (non-optional version).
        """
        return 0.0 if abs(value) < self.tolerance else float(value)
    
    def map_result(self, solver_result: Dict[str, Any], 
                  variables: List[str],
                  objective_type: str = "minimize") -> LPSolution:
        """
        Map solver output to structured result (STEP-3).
        
        Args:
            solver_result: Raw result from LPSolver
            variables: Variable names in order
            objective_type: "minimize" or "maximize"
            
        Returns:
            Structured LPSolution
        """
        # Determine status
        status = self._determine_status(solver_result)
        
        # Extract objective value
        objective = None
        if solver_result.get('fun') is not None:
            objective = self._cleanup_float(solver_result['fun'])
            # If we were maximizing but solver minimized -c, adjust sign
            # Note: LPSolver already handles this internally
        
        # Extract solution values
        solution_dict = {}
        if solver_result.get('x') is not None and status == "optimal":
            x_values = solver_result['x']
            for var_name, value in zip(variables, x_values):
                solution_dict[var_name] = self._cleanup_float_value(value)
        
        # Compute usefulness range if applicable
        usefulness_range = None
        if status == "optimal" and 'r' in solution_dict:
            usefulness_range = self._compute_usefulness_range(solution_dict)
        
        # Extract solver info
        solver_info = {
            'message': solver_result.get('message', ''),
            'iterations': solver_result.get('iterations', 0),
            'success': solver_result.get('success', False),
            'status_code': solver_result.get('status', -1)
        }
        
        return LPSolution(
            status=status,
            objective=objective,
            solution=solution_dict,
            usefulness_range=usefulness_range,
            solver_info=solver_info,
            variables=variables.copy()
        )
    
    def _determine_status(self, solver_result: Dict[str, Any]) -> str:
        """
        Determine problem status from solver result (STEP-5).
        
        Args:
            solver_result: Raw solver result
            
        Returns:
            Status string: "optimal", "infeasible", "unbounded", "failed"
        """
        success = solver_result.get('success', False)
        status_code = solver_result.get('status', -1)
        message = str(solver_result.get('message', '')).lower()
        
        if success:
            return "optimal"
        
        # Check for infeasible
        if status_code == 2 or 'infeasible' in message:
            return "infeasible"
        
        # Check for unbounded
        if status_code == 3 or 'unbounded' in message:
            return "unbounded"
        
        # Default to failed
        return "failed"
    
    def _compute_usefulness_range(self, solution: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """
        Compute usefulness range for paving-type models (STEP-4).
        
        Formula: xj* − r* <= xj <= xj* + r*
        
        Args:
            solution: Dictionary of variable values
            
        Returns:
            Dictionary mapping variable names to (low, high) intervals
        """
        if 'r' not in solution:
            return {}
        
        r_star = solution['r']
        usefulness_range = {}
        
        for var_name, value in solution.items():
            if var_name != 'r':
                low = self._cleanup_float_value(value - r_star)
                high = self._cleanup_float_value(value + r_star)
                usefulness_range[var_name] = (low, high)
        
        return usefulness_range
    
    def solve_complete(self, matrices: Dict[str, Any], 
                      objective_type: str = "minimize") -> Dict[str, Any]:
        """
        Complete solve pipeline: matrices → solver → structured result.
        
        Args:
            matrices: Dictionary from MatrixBuilderV3
            objective_type: "minimize" or "maximize"
            
        Returns:
            Dictionary with structured result
        """
        # Step 1: Solve LP
        solver_result = self.solve_lp(matrices, objective_type)
        
        # Step 2: Map result
        variables = matrices.get('variables', [])
        solution = self.map_result(solver_result, variables, objective_type)
        
        # Convert to dictionary format
        return {
            'status': solution.status,
            'objective': solution.objective,
            'solution': solution.solution,
            'usefulness_range': solution.usefulness_range,
            'solver_info': solution.solver_info,
            'variables': solution.variables
        }


# Convenience function
def solve_lp_matrices(matrices: Dict[str, Any], 
                     objective_type: str = "minimize") -> Dict[str, Any]:
    """
    Convenience function to solve LP from matrices.
    
    Args:
        matrices: Dictionary from MatrixBuilderV3
        objective_type: "minimize" or "maximize"
        
    Returns:
        Dictionary with structured result
    """
    engine = LPSolverEngine()
    return engine.solve_complete(matrices, objective_type)
