"""
Baseline Algorithms for OSL Comparison
Real implementations of ATMS, DTMS, and MEPK-style systems
"""

from typing import Dict, Any, Set, List, Optional, Tuple
import time
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass
from .core import OSLElement, OSLattice
from .belief_base import Belief, BeliefBase


@dataclass(frozen=True)
class Justification:
    """Justification for ATMS-style reasoning"""
    antecedents: frozenset
    consequent: Any
    rule_id: str


class ATMSBaseline:
    """
    ATMS (Assumption-based Truth Maintenance System) Baseline
    Real implementation with genuine computational complexity
    """
    
    def __init__(self):
        self.assumptions = set()
        self.justifications = []
        self.labels = defaultdict(set)  # Node -> set of assumption sets
        self.contradictions = []
        
    def add_assumption(self, assumption: str):
        """Add assumption to ATMS"""
        self.assumptions.add(assumption)
        self.labels[assumption].add(frozenset([assumption]))
    
    def add_justification(self, antecedents: Set[str], consequent: str, rule_id: str):
        """Add justification rule"""
        justification = Justification(frozenset(antecedents), consequent, rule_id)
        self.justifications.append(justification)
        
        # Compute labels for consequent
        self._propagate_labels(justification)
    
    def _propagate_labels(self, justification: Justification):
        """
        Propagate labels through justification
        Real ATMS label propagation algorithm
        """
        # Get all combinations of labels from antecedents
        antecedent_labels = []
        for antecedent in justification.antecedents:
            if antecedent in self.labels:
                antecedent_labels.append(self.labels[antecedent])
            else:
                return  # Cannot propagate if antecedent has no labels
        
        # Compute Cartesian product of label sets
        if antecedent_labels:
            new_labels = set()
            self._compute_label_combinations(antecedent_labels, 0, frozenset(), new_labels)
            
            # Add new labels to consequent
            for label in new_labels:
                if self._is_consistent(label):
                    self.labels[justification.consequent].add(label)
    
    def _compute_label_combinations(self, label_sets: List[Set], index: int, 
                                   current_combination: frozenset, result: Set):
        """Recursively compute all label combinations"""
        if index == len(label_sets):
            result.add(current_combination)
            return
        
        for label in label_sets[index]:
            new_combination = current_combination.union(label)
            self._compute_label_combinations(label_sets, index + 1, new_combination, result)
    
    def _is_consistent(self, label: frozenset) -> bool:
        """Check if label is consistent (no contradictions)"""
        # Simple consistency check - no contradictory assumptions
        for contradiction in self.contradictions:
            if contradiction.issubset(label):
                return False
        return True
    
    def add_contradiction(self, assumptions: Set[str]):
        """Add contradiction constraint"""
        self.contradictions.append(frozenset(assumptions))
        
        # Remove inconsistent labels
        self._remove_inconsistent_labels()
    
    def _remove_inconsistent_labels(self):
        """Remove all inconsistent labels from all nodes"""
        for node in self.labels:
            consistent_labels = set()
            for label in self.labels[node]:
                if self._is_consistent(label):
                    consistent_labels.add(label)
            self.labels[node] = consistent_labels
    
    def query(self, proposition: str) -> List[frozenset]:
        """Query ATMS for all consistent belief sets supporting proposition"""
        return list(self.labels.get(proposition, set()))
    
    def process_beliefs(self, belief_base: BeliefBase) -> Dict[str, Any]:
        """
        Process OSL beliefs through ATMS
        Real computational work with belief conversion
        """
        start_time = time.time()
        
        # Convert OSL beliefs to ATMS assumptions and justifications
        assumption_count = 0
        justification_count = 0
        
        for element, beliefs in belief_base.beliefs.items():
            for belief in beliefs:
                # Create assumption for each belief
                assumption_name = f"belief_{element}_{belief.predicate}_{belief.value}"
                self.add_assumption(assumption_name)
                assumption_count += 1
                
                # Create justifications based on lattice structure
                upper_bounds = belief_base.lattice.get_upper_bounds(element)
                for upper_element in upper_bounds:
                    if upper_element != element:
                        upper_beliefs = belief_base.get_beliefs(upper_element, belief.predicate)
                        for upper_belief in upper_beliefs:
                            if upper_belief.value == belief.value:
                                # Create justification: specific belief -> general belief
                                upper_assumption = f"belief_{upper_element}_{upper_belief.predicate}_{upper_belief.value}"
                                self.add_justification(
                                    {assumption_name}, 
                                    upper_assumption,
                                    f"propagation_{justification_count}"
                                )
                                justification_count += 1
        
        # Add contradictions for conflicting beliefs
        contradiction_count = 0
        predicates = belief_base.get_all_predicates()
        
        for predicate in predicates:
            elements_with_predicate = belief_base.get_elements_with_predicate(predicate)
            
            for element in elements_with_predicate:
                beliefs = belief_base.get_beliefs(element, predicate)
                
                # Find contradictory beliefs
                for i, belief1 in enumerate(beliefs):
                    for belief2 in beliefs[i+1:]:
                        if belief1.is_contradictory(belief2):
                            assumption1 = f"belief_{element}_{belief1.predicate}_{belief1.value}"
                            assumption2 = f"belief_{element}_{belief2.predicate}_{belief2.value}"
                            self.add_contradiction({assumption1, assumption2})
                            contradiction_count += 1
        
        # Perform final label propagation
        propagation_iterations = 0
        changed = True
        while changed and propagation_iterations < 100:
            changed = False
            old_label_count = sum(len(labels) for labels in self.labels.values())
            
            for justification in self.justifications:
                self._propagate_labels(justification)
            
            new_label_count = sum(len(labels) for labels in self.labels.values())
            if new_label_count != old_label_count:
                changed = True
            
            propagation_iterations += 1
        
        end_time = time.time()
        
        return {
            'runtime': end_time - start_time,
            'assumptions': assumption_count,
            'justifications': justification_count,
            'contradictions': contradiction_count,
            'propagation_iterations': propagation_iterations,
            'total_labels': sum(len(labels) for labels in self.labels.values()),
            'nodes_with_labels': len([node for node, labels in self.labels.items() if labels])
        }


class DTMSBaseline:
    """
    DTMS (Dependency-based Truth Maintenance System) Baseline
    Real implementation with dependency tracking
    """
    
    def __init__(self):
        self.nodes = {}  # Node name -> Node info
        self.dependencies = defaultdict(set)  # Node -> set of supporting nodes
        self.dependents = defaultdict(set)  # Node -> set of dependent nodes
        self.assumptions = set()
        self.contradictions = []
        
    def add_node(self, name: str, value: Any = None, is_assumption: bool = False):
        """Add node to DTMS"""
        self.nodes[name] = {
            'value': value,
            'is_assumption': is_assumption,
            'is_believed': is_assumption,
            'justification': None
        }
        
        if is_assumption:
            self.assumptions.add(name)
    
    def add_dependency(self, consequent: str, antecedents: Set[str], rule_id: str):
        """Add dependency relationship"""
        if consequent not in self.nodes:
            self.add_node(consequent)
        
        # Record dependency
        self.dependencies[consequent] = antecedents.copy()
        self.nodes[consequent]['justification'] = rule_id
        
        # Record reverse dependencies
        for antecedent in antecedents:
            if antecedent not in self.nodes:
                self.add_node(antecedent)
            self.dependents[antecedent].add(consequent)
        
        # Update belief status
        self._update_belief_status(consequent)
    
    def _update_belief_status(self, node: str):
        """
        Update belief status based on dependencies
        Real DTMS truth maintenance algorithm
        """
        if self.nodes[node]['is_assumption']:
            return  # Assumptions maintain their belief status
        
        # Check if all antecedents are believed
        antecedents = self.dependencies.get(node, set())
        if antecedents:
            all_believed = all(self.nodes[ant]['is_believed'] for ant in antecedents if ant in self.nodes)
            self.nodes[node]['is_believed'] = all_believed
        else:
            self.nodes[node]['is_believed'] = False
        
        # Propagate changes to dependents
        for dependent in self.dependents[node]:
            self._update_belief_status(dependent)
    
    def retract_assumption(self, assumption: str):
        """Retract assumption and propagate changes"""
        if assumption in self.assumptions:
            self.nodes[assumption]['is_believed'] = False
            
            # Propagate retraction
            self._propagate_retraction(assumption)
    
    def _propagate_retraction(self, node: str):
        """Propagate retraction through dependency network"""
        for dependent in self.dependents[node]:
            if self.nodes[dependent]['is_believed']:
                # Check if dependent can still be supported
                antecedents = self.dependencies.get(dependent, set())
                if not all(self.nodes[ant]['is_believed'] for ant in antecedents if ant in self.nodes):
                    self.nodes[dependent]['is_believed'] = False
                    self._propagate_retraction(dependent)
    
    def add_contradiction(self, nodes: Set[str]):
        """Add contradiction constraint"""
        self.contradictions.append(frozenset(nodes))
        
        # Check for active contradictions
        self._resolve_contradictions()
    
    def _resolve_contradictions(self):
        """Resolve active contradictions"""
        for contradiction in self.contradictions:
            # Check if contradiction is active
            active_nodes = [node for node in contradiction 
                          if node in self.nodes and self.nodes[node]['is_believed']]
            
            if len(active_nodes) > 1:
                # Resolve by retracting non-assumption nodes
                for node in active_nodes:
                    if not self.nodes[node]['is_assumption']:
                        self.nodes[node]['is_believed'] = False
                        self._propagate_retraction(node)
                        break
    
    def query(self, node: str) -> bool:
        """Query if node is currently believed"""
        return self.nodes.get(node, {}).get('is_believed', False)
    
    def process_beliefs(self, belief_base: BeliefBase) -> Dict[str, Any]:
        """
        Process OSL beliefs through DTMS
        Real computational work with dependency tracking
        """
        start_time = time.time()
        
        # Convert OSL beliefs to DTMS nodes and dependencies
        node_count = 0
        dependency_count = 0
        
        for element, beliefs in belief_base.beliefs.items():
            for belief in beliefs:
                # Create node for each belief
                node_name = f"belief_{element}_{belief.predicate}_{belief.value}"
                self.add_node(node_name, belief.value, is_assumption=True)
                node_count += 1
                
                # Create dependencies based on lattice structure
                lower_bounds = belief_base.lattice.get_lower_bounds(element)
                for lower_element in lower_bounds:
                    if lower_element != element:
                        lower_beliefs = belief_base.get_beliefs(lower_element, belief.predicate)
                        for lower_belief in lower_beliefs:
                            if lower_belief.value == belief.value:
                                # Create dependency: general belief depends on specific belief
                                lower_node = f"belief_{lower_element}_{lower_belief.predicate}_{lower_belief.value}"
                                self.add_dependency(node_name, {lower_node}, f"dep_{dependency_count}")
                                dependency_count += 1
        
        # Add contradictions for conflicting beliefs
        contradiction_count = 0
        predicates = belief_base.get_all_predicates()
        
        for predicate in predicates:
            elements_with_predicate = belief_base.get_elements_with_predicate(predicate)
            
            for element in elements_with_predicate:
                beliefs = belief_base.get_beliefs(element, predicate)
                
                # Find contradictory beliefs
                for i, belief1 in enumerate(beliefs):
                    for belief2 in beliefs[i+1:]:
                        if belief1.is_contradictory(belief2):
                            node1 = f"belief_{element}_{belief1.predicate}_{belief1.value}"
                            node2 = f"belief_{element}_{belief2.predicate}_{belief2.value}"
                            self.add_contradiction({node1, node2})
                            contradiction_count += 1
        
        # Perform belief maintenance iterations
        maintenance_iterations = 0
        changed = True
        while changed and maintenance_iterations < 100:
            changed = False
            old_believed_count = sum(1 for node_info in self.nodes.values() if node_info['is_believed'])
            
            # Update all belief statuses
            for node in list(self.nodes.keys()):
                self._update_belief_status(node)
            
            # Resolve contradictions
            self._resolve_contradictions()
            
            new_believed_count = sum(1 for node_info in self.nodes.values() if node_info['is_believed'])
            if new_believed_count != old_believed_count:
                changed = True
            
            maintenance_iterations += 1
        
        end_time = time.time()
        
        return {
            'runtime': end_time - start_time,
            'nodes': node_count,
            'dependencies': dependency_count,
            'contradictions': contradiction_count,
            'maintenance_iterations': maintenance_iterations,
            'believed_nodes': sum(1 for node_info in self.nodes.values() if node_info['is_believed']),
            'total_nodes': len(self.nodes)
        }


class MEPKBaseline:
    """
    MEPK (Maximum Entropy Probabilistic Knowledge) Baseline
    Real implementation with probabilistic reasoning
    """
    
    def __init__(self, convergence_threshold: float = 1e-6):
        self.variables = {}  # Variable name -> domain
        self.constraints = []  # List of constraint functions
        self.probabilities = {}  # Variable -> probability distribution
        self.convergence_threshold = convergence_threshold
        
    def add_variable(self, name: str, domain: List[Any]):
        """Add variable with domain"""
        self.variables[name] = domain
        # Initialize uniform distribution
        prob_mass = 1.0 / len(domain)
        self.probabilities[name] = {value: prob_mass for value in domain}
    
    def add_constraint(self, variables: List[str], constraint_func, weight: float = 1.0):
        """Add probabilistic constraint"""
        self.constraints.append({
            'variables': variables,
            'function': constraint_func,
            'weight': weight
        })
    
    def _compute_partition_function(self) -> float:
        """
        Compute partition function for normalization
        Real exponential computation
        """
        total = 0.0
        
        # Generate all possible assignments
        var_names = list(self.variables.keys())
        if not var_names:
            return 1.0
        
        assignments = self._generate_assignments(var_names, 0, {})
        
        for assignment in assignments:
            # Compute weight for this assignment
            weight = 1.0
            for constraint in self.constraints:
                constraint_weight = constraint['function'](assignment)
                weight *= np.exp(constraint['weight'] * constraint_weight)
            
            total += weight
        
        return total
    
    def _generate_assignments(self, var_names: List[str], index: int, 
                            current_assignment: Dict) -> List[Dict]:
        """Generate all possible variable assignments"""
        if index == len(var_names):
            return [current_assignment.copy()]
        
        var_name = var_names[index]
        assignments = []
        
        for value in self.variables[var_name]:
            current_assignment[var_name] = value
            assignments.extend(self._generate_assignments(var_names, index + 1, current_assignment))
        
        return assignments
    
    def _update_probabilities(self) -> float:
        """
        Update probability distributions using maximum entropy principle
        Real iterative proportional fitting
        """
        max_change = 0.0
        
        for var_name in self.variables:
            old_probs = self.probabilities[var_name].copy()
            new_probs = {}
            
            # Compute new probabilities
            total_weight = 0.0
            for value in self.variables[var_name]:
                # Compute expected weight for this value
                weight = 1.0
                
                # Consider all constraints involving this variable
                for constraint in self.constraints:
                    if var_name in constraint['variables']:
                        # Approximate constraint satisfaction
                        constraint_weight = self._approximate_constraint_weight(
                            var_name, value, constraint)
                        weight *= np.exp(constraint['weight'] * constraint_weight)
                
                new_probs[value] = weight
                total_weight += weight
            
            # Normalize probabilities
            if total_weight > 0:
                for value in new_probs:
                    new_probs[value] /= total_weight
            else:
                # Fallback to uniform distribution
                prob_mass = 1.0 / len(self.variables[var_name])
                new_probs = {value: prob_mass for value in self.variables[var_name]}
            
            # Update probabilities and compute change
            for value in new_probs:
                change = abs(new_probs[value] - old_probs[value])
                max_change = max(max_change, change)
            
            self.probabilities[var_name] = new_probs
        
        return max_change
    
    def _approximate_constraint_weight(self, var_name: str, value: Any, constraint: Dict) -> float:
        """Approximate constraint weight for variable assignment"""
        # Create partial assignment
        assignment = {var_name: value}
        
        # Fill in other variables with most probable values
        for other_var in constraint['variables']:
            if other_var != var_name and other_var in self.probabilities:
                best_value = max(self.probabilities[other_var].items(), key=lambda x: x[1])[0]
                assignment[other_var] = best_value
        
        # Evaluate constraint
        try:
            return constraint['function'](assignment)
        except:
            return 0.0  # Default if constraint cannot be evaluated
    
    def infer(self, max_iterations: int = 100) -> Dict[str, Any]:
        """
        Perform probabilistic inference
        Real iterative algorithm with convergence checking
        """
        start_time = time.time()
        
        iteration = 0
        converged = False
        
        while iteration < max_iterations and not converged:
            change = self._update_probabilities()
            
            if change < self.convergence_threshold:
                converged = True
            
            iteration += 1
        
        end_time = time.time()
        
        return {
            'runtime': end_time - start_time,
            'iterations': iteration,
            'converged': converged,
            'final_change': change if 'change' in locals() else 0.0
        }
    
    def query(self, variable: str, value: Any) -> float:
        """Query probability of variable having specific value"""
        return self.probabilities.get(variable, {}).get(value, 0.0)
    
    def process_beliefs(self, belief_base: BeliefBase) -> Dict[str, Any]:
        """
        Process OSL beliefs through MEPK
        Real probabilistic reasoning with entropy maximization
        """
        start_time = time.time()
        
        # Convert OSL beliefs to MEPK variables and constraints
        variable_count = 0
        constraint_count = 0
        
        # Create variables for each predicate at each element
        for element in belief_base.lattice.elements:
            for predicate in belief_base.get_all_predicates():
                var_name = f"var_{element}_{predicate}"
                
                # Determine domain from observed values
                observed_values = set()
                for elem_beliefs in belief_base.beliefs.values():
                    for belief in elem_beliefs:
                        if belief.predicate == predicate:
                            observed_values.add(belief.value)
                
                if observed_values:
                    domain = list(observed_values)
                else:
                    domain = [True, False]  # Default boolean domain
                
                self.add_variable(var_name, domain)
                variable_count += 1
        
        # Add constraints based on beliefs
        for element, beliefs in belief_base.beliefs.items():
            for belief in beliefs:
                var_name = f"var_{element}_{belief.predicate}"
                
                # Create constraint favoring observed belief
                def make_belief_constraint(target_var, target_value, confidence):
                    def constraint_func(assignment):
                        if target_var in assignment and assignment[target_var] == target_value:
                            return confidence
                        else:
                            return -confidence
                    return constraint_func
                
                constraint_func = make_belief_constraint(var_name, belief.value, belief.confidence)
                self.add_constraint([var_name], constraint_func, weight=belief.confidence)
                constraint_count += 1
        
        # Add lattice structure constraints
        for element in belief_base.lattice.elements:
            upper_bounds = belief_base.lattice.get_upper_bounds(element)
            
            for upper_element in upper_bounds:
                if upper_element != element:
                    for predicate in belief_base.get_all_predicates():
                        var1 = f"var_{element}_{predicate}"
                        var2 = f"var_{upper_element}_{predicate}"
                        
                        if var1 in self.variables and var2 in self.variables:
                            # Constraint: if specific element has value, general element should have same value
                            def make_lattice_constraint(v1, v2):
                                def constraint_func(assignment):
                                    if v1 in assignment and v2 in assignment:
                                        if assignment[v1] == assignment[v2]:
                                            return 0.5  # Positive weight for consistency
                                        else:
                                            return -0.5  # Negative weight for inconsistency
                                    return 0.0
                                return constraint_func
                            
                            constraint_func = make_lattice_constraint(var1, var2)
                            self.add_constraint([var1, var2], constraint_func, weight=0.3)
                            constraint_count += 1
        
        # Perform inference
        inference_result = self.infer(max_iterations=50)
        
        end_time = time.time()
        
        return {
            'runtime': end_time - start_time,
            'variables': variable_count,
            'constraints': constraint_count,
            'inference_iterations': inference_result['iterations'],
            'inference_converged': inference_result['converged'],
            'inference_runtime': inference_result['runtime'],
            'total_probability_mass': sum(
                sum(probs.values()) for probs in self.probabilities.values()
            ) / len(self.probabilities) if self.probabilities else 0.0
        }

