"""
Core Observer-Situation Lattice implementation.

This module implements the fundamental lattice structure that forms the basis
of the OSL framework. The lattice is constructed as a Cartesian product of
observer and situation partial orders.
"""

import itertools
from typing import List, Tuple, Set, Dict, Any, Optional
import networkx as nx
from functools import lru_cache


class OSLattice:
    """
    Observer-Situation Lattice implementation.
    
    A finite complete lattice formed as the Cartesian product of observer
    and situation partial orders: E = O × Σ
    """
    
    def __init__(self, observers: List[str], situations: List[str], 
                 observer_order: Optional[List[Tuple[str, str]]] = None,
                 situation_order: Optional[List[Tuple[str, str]]] = None):
        """
        Initialize the Observer-Situation Lattice.
        
        Args:
            observers: List of observer identifiers
            situations: List of situation identifiers  
            observer_order: List of (a, b) tuples where a ≼ b in observer order
            situation_order: List of (a, b) tuples where a ≼ b in situation order
        """
        self.observers = observers
        self.situations = situations
        
        # Build observer partial order
        self.observer_graph = nx.DiGraph()
        self.observer_graph.add_nodes_from(observers)
        if observer_order:
            self.observer_graph.add_edges_from(observer_order)
        
        # Build situation partial order  
        self.situation_graph = nx.DiGraph()
        self.situation_graph.add_nodes_from(situations)
        if situation_order:
            self.situation_graph.add_edges_from(situation_order)
            
        # Compute transitive closures for efficient ordering queries
        self.observer_closure = nx.transitive_closure(self.observer_graph)
        self.situation_closure = nx.transitive_closure(self.situation_graph)
        
        # Add reflexivity
        for obs in observers:
            self.observer_closure.add_edge(obs, obs)
        for sit in situations:
            self.situation_closure.add_edge(sit, sit)
            
        # Generate all lattice elements
        self.elements = list(itertools.product(observers, situations))
        self.element_set = set(self.elements)
        
        # Build element ordering relation
        self._build_element_order()
        
        # Verify lattice properties
        self._verify_lattice_properties()
    
    def _build_element_order(self):
        """Build the partial order on lattice elements."""
        self.element_graph = nx.DiGraph()
        self.element_graph.add_nodes_from(self.elements)
        
        # Add edges based on component-wise ordering
        for e1 in self.elements:
            for e2 in self.elements:
                if self.leq(e1, e2) and e1 != e2:
                    self.element_graph.add_edge(e1, e2)
        
        # Compute transitive closure
        self.element_closure = nx.transitive_closure(self.element_graph)
        
        # Add reflexivity
        for elem in self.elements:
            self.element_closure.add_edge(elem, elem)
    
    def _verify_lattice_properties(self):
        """Verify that the structure forms a complete lattice."""
        # Check reflexivity
        for elem in self.elements:
            if not self.leq(elem, elem):
                raise ValueError(f"Lattice not reflexive: {elem}")
        
        # Check antisymmetry  
        for e1 in self.elements:
            for e2 in self.elements:
                if self.leq(e1, e2) and self.leq(e2, e1) and e1 != e2:
                    raise ValueError(f"Lattice not antisymmetric: {e1}, {e2}")
        
        # Check transitivity
        for e1 in self.elements:
            for e2 in self.elements:
                for e3 in self.elements:
                    if self.leq(e1, e2) and self.leq(e2, e3) and not self.leq(e1, e3):
                        raise ValueError(f"Lattice not transitive: {e1}, {e2}, {e3}")
    
    def leq(self, e1: Tuple[str, str], e2: Tuple[str, str]) -> bool:
        """
        Check if e1 ≼ e2 in the lattice ordering.
        
        Args:
            e1, e2: Lattice elements as (observer, situation) tuples
            
        Returns:
            True if e1 ≼ e2, False otherwise
        """
        if e1 not in self.element_set or e2 not in self.element_set:
            return False
            
        o1, s1 = e1
        o2, s2 = e2
        
        # Component-wise ordering
        obs_leq = self.observer_closure.has_edge(o1, o2)
        sit_leq = self.situation_closure.has_edge(s1, s2)
        
        return obs_leq and sit_leq
    
    def lt(self, e1: Tuple[str, str], e2: Tuple[str, str]) -> bool:
        """Check if e1 ≺ e2 (strict ordering)."""
        return self.leq(e1, e2) and e1 != e2
    
    @lru_cache(maxsize=1024)
    def join(self, e1: Tuple[str, str], e2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Compute the join (least upper bound) of two elements.
        
        Args:
            e1, e2: Lattice elements
            
        Returns:
            The join e1 ∨ e2
        """
        if e1 == e2:
            return e1
            
        # Find all upper bounds
        upper_bounds = []
        for elem in self.elements:
            if self.leq(e1, elem) and self.leq(e2, elem):
                upper_bounds.append(elem)
        
        if not upper_bounds:
            raise ValueError(f"No upper bounds found for {e1} and {e2}")
        
        # Find minimal upper bounds
        minimal_bounds = []
        for ub in upper_bounds:
            is_minimal = True
            for other_ub in upper_bounds:
                if other_ub != ub and self.leq(other_ub, ub):
                    is_minimal = False
                    break
            if is_minimal:
                minimal_bounds.append(ub)
        
        if len(minimal_bounds) != 1:
            raise ValueError(f"Join not unique for {e1} and {e2}: {minimal_bounds}")
        
        return minimal_bounds[0]
    
    @lru_cache(maxsize=1024)  
    def meet(self, e1: Tuple[str, str], e2: Tuple[str, str]) -> Tuple[str, str]:
        """
        Compute the meet (greatest lower bound) of two elements.
        
        Args:
            e1, e2: Lattice elements
            
        Returns:
            The meet e1 ∧ e2
        """
        if e1 == e2:
            return e1
            
        # Find all lower bounds
        lower_bounds = []
        for elem in self.elements:
            if self.leq(elem, e1) and self.leq(elem, e2):
                lower_bounds.append(elem)
        
        if not lower_bounds:
            raise ValueError(f"No lower bounds found for {e1} and {e2}")
        
        # Find maximal lower bounds
        maximal_bounds = []
        for lb in lower_bounds:
            is_maximal = True
            for other_lb in lower_bounds:
                if other_lb != lb and self.leq(lb, other_lb):
                    is_maximal = False
                    break
            if is_maximal:
                maximal_bounds.append(lb)
        
        if len(maximal_bounds) != 1:
            raise ValueError(f"Meet not unique for {e1} and {e2}: {maximal_bounds}")
        
        return maximal_bounds[0]
    
    @lru_cache(maxsize=512)
    def ancestors(self, elem: Tuple[str, str]) -> Set[Tuple[str, str]]:
        """Get all ancestors of an element (elements ≽ elem)."""
        ancestors = set()
        for e in self.elements:
            if self.leq(elem, e):
                ancestors.add(e)
        return ancestors
    
    @lru_cache(maxsize=512)
    def descendants(self, elem: Tuple[str, str]) -> Set[Tuple[str, str]]:
        """Get all descendants of an element (elements ≼ elem).""" 
        descendants = set()
        for e in self.elements:
            if self.leq(e, elem):
                descendants.add(e)
        return descendants
    
    def get_top(self) -> Tuple[str, str]:
        """Get the top element of the lattice."""
        # Top element has maximum observer and situation
        top_obs = None
        top_sit = None
        
        # Find observer with no outgoing edges (maximal)
        for obs in self.observers:
            if self.observer_graph.out_degree(obs) == 0:
                if top_obs is None:
                    top_obs = obs
                else:
                    # Multiple maximal elements - find their join
                    # For simplicity, assume single maximal element
                    pass
        
        # Find situation with no outgoing edges (maximal)  
        for sit in self.situations:
            if self.situation_graph.out_degree(sit) == 0:
                if top_sit is None:
                    top_sit = sit
                else:
                    # Multiple maximal elements
                    pass
        
        if top_obs is None:
            top_obs = self.observers[-1]  # Fallback
        if top_sit is None:
            top_sit = self.situations[-1]  # Fallback
            
        return (top_obs, top_sit)
    
    def get_bottom(self) -> Tuple[str, str]:
        """Get the bottom element of the lattice."""
        # Bottom element has minimum observer and situation
        bottom_obs = None
        bottom_sit = None
        
        # Find observer with no incoming edges (minimal)
        for obs in self.observers:
            if self.observer_graph.in_degree(obs) == 0:
                if bottom_obs is None:
                    bottom_obs = obs
                else:
                    # Multiple minimal elements
                    pass
        
        # Find situation with no incoming edges (minimal)
        for sit in self.situations:
            if self.situation_graph.in_degree(sit) == 0:
                if bottom_sit is None:
                    bottom_sit = sit
                else:
                    # Multiple minimal elements
                    pass
        
        if bottom_obs is None:
            bottom_obs = self.observers[0]  # Fallback
        if bottom_sit is None:
            bottom_sit = self.situations[0]  # Fallback
            
        return (bottom_obs, bottom_sit)
    
    def size(self) -> int:
        """Get the number of elements in the lattice."""
        return len(self.elements)
    
    def height(self) -> int:
        """Get the height of the lattice (length of longest chain)."""
        try:
            return nx.dag_longest_path_length(self.element_graph) + 1
        except:
            # Fallback calculation
            max_chain = 0
            for elem in self.elements:
                chain_length = len(self.ancestors(elem))
                max_chain = max(max_chain, chain_length)
            return max_chain
    
    def width(self) -> int:
        """Get the width of the lattice (size of largest antichain)."""
        # This is computationally expensive for large lattices
        # For now, return a simple estimate
        return min(len(self.observers), len(self.situations))
    
    def is_balanced(self, kappa: float = 2.0) -> bool:
        """
        Check if the lattice is κ-balanced.
        
        A lattice is κ-balanced if max{|ancestors(e)|, |descendants(e)|} ≤ κ√|E|
        """
        threshold = kappa * (self.size() ** 0.5)
        
        for elem in self.elements:
            if len(self.ancestors(elem)) > threshold:
                return False
            if len(self.descendants(elem)) > threshold:
                return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of the lattice."""
        return f"OSLattice({len(self.observers)} observers, {len(self.situations)} situations, {self.size()} elements)"
    
    def __repr__(self) -> str:
        return self.__str__()

