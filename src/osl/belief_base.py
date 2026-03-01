"""
OSL Belief Base - Real Implementation
Manages beliefs associated with lattice elements with genuine operations
"""

from typing import Dict, Any, Set, List, Optional, Tuple, Union
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from .core import OSLElement, OSLattice


@dataclass(frozen=True)
class Belief:
    """
    Individual belief with predicate, value, and confidence
    """
    predicate: str
    value: Any
    confidence: float = 1.0
    source: Optional[str] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        # Validate confidence is in [0, 1]
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be in [0, 1], got {self.confidence}")
        
        # Convert mutable values to immutable for hashing
        if isinstance(self.value, list):
            object.__setattr__(self, 'value', tuple(self.value))
        elif isinstance(self.value, dict):
            object.__setattr__(self, 'value', tuple(sorted(self.value.items())))
        elif isinstance(self.value, set):
            object.__setattr__(self, 'value', frozenset(self.value))
    
    def is_contradictory(self, other: 'Belief') -> bool:
        """
        Check if this belief contradicts another belief
        Real logical contradiction detection
        """
        if self.predicate != other.predicate:
            return False
        
        # Handle boolean contradictions
        if isinstance(self.value, bool) and isinstance(other.value, bool):
            return self.value != other.value
        
        # Handle numeric contradictions (with tolerance)
        if isinstance(self.value, (int, float)) and isinstance(other.value, (int, float)):
            # Consider values contradictory if they differ significantly
            tolerance = 0.1
            return abs(self.value - other.value) > tolerance
        
        # Handle string contradictions
        if isinstance(self.value, str) and isinstance(other.value, str):
            return self.value != other.value
        
        # Default: different types or values are contradictory
        return self.value != other.value
    
    def combine_with(self, other: 'Belief', method: str = 'average') -> 'Belief':
        """
        Combine this belief with another belief on the same predicate
        Real belief fusion operations
        """
        if self.predicate != other.predicate:
            raise ValueError("Cannot combine beliefs with different predicates")
        
        if method == 'average':
            # Weighted average by confidence
            total_confidence = self.confidence + other.confidence
            if total_confidence == 0:
                combined_confidence = 0.0
                combined_value = self.value
            else:
                combined_confidence = min(1.0, total_confidence / 2.0)
                
                # Combine values based on type
                if isinstance(self.value, bool) and isinstance(other.value, bool):
                    # For booleans, use confidence-weighted voting
                    if self.confidence > other.confidence:
                        combined_value = self.value
                    elif other.confidence > self.confidence:
                        combined_value = other.value
                    else:
                        combined_value = self.value  # Tie-breaking
                elif isinstance(self.value, (int, float)) and isinstance(other.value, (int, float)):
                    # For numbers, use weighted average
                    combined_value = (self.value * self.confidence + other.value * other.confidence) / total_confidence
                else:
                    # For other types, use higher confidence value
                    combined_value = self.value if self.confidence >= other.confidence else other.value
        
        elif method == 'maximum':
            # Take belief with maximum confidence
            if self.confidence >= other.confidence:
                return Belief(self.predicate, self.value, self.confidence, self.source, self.timestamp)
            else:
                return Belief(other.predicate, other.value, other.confidence, other.source, other.timestamp)
        
        elif method == 'minimum':
            # Take belief with minimum confidence (most conservative)
            if self.confidence <= other.confidence:
                return Belief(self.predicate, self.value, self.confidence, self.source, self.timestamp)
            else:
                return Belief(other.predicate, other.value, other.confidence, other.source, other.timestamp)
        
        else:
            raise ValueError(f"Unknown combination method: {method}")
        
        return Belief(self.predicate, combined_value, combined_confidence, 
                     f"combined({self.source},{other.source})", None)


class BeliefBase:
    """
    Belief Base for OSL Framework
    Manages beliefs associated with lattice elements with real operations
    """
    
    def __init__(self, lattice: OSLattice):
        self.lattice = lattice
        # Map from OSLElement to list of beliefs
        self.beliefs: Dict[OSLElement, List[Belief]] = defaultdict(list)
        # Index by predicate for fast lookup
        self.predicate_index: Dict[str, Dict[OSLElement, List[Belief]]] = defaultdict(lambda: defaultdict(list))
        # Contradiction tracking
        self.contradictions: List[Tuple[OSLElement, Belief, OSLElement, Belief]] = []
        
    def add_belief(self, element: OSLElement, predicate: str, value: Any, 
                  confidence: float = 1.0, source: Optional[str] = None) -> bool:
        """
        Add belief to element with real validation and indexing
        Returns True if belief was added, False if rejected due to contradiction
        """
        if element not in self.lattice.elements:
            raise ValueError(f"Element {element} not in lattice")
        
        belief = Belief(predicate, value, confidence, source)
        
        # Check for contradictions with existing beliefs on same element
        existing_beliefs = self.get_beliefs(element, predicate)
        for existing in existing_beliefs:
            if belief.is_contradictory(existing):
                # Record contradiction
                self.contradictions.append((element, belief, element, existing))
                # Decide whether to add contradictory belief
                if confidence > existing.confidence:
                    # Replace with higher confidence belief
                    self.beliefs[element] = [b for b in self.beliefs[element] if b != existing]
                    self.predicate_index[predicate][element] = [b for b in self.predicate_index[predicate][element] if b != existing]
                else:
                    # Reject lower confidence contradictory belief
                    return False
        
        # Add belief
        self.beliefs[element].append(belief)
        self.predicate_index[predicate][element].append(belief)
        
        return True
    
    def get_beliefs(self, element: OSLElement, predicate: Optional[str] = None) -> List[Belief]:
        """
        Get beliefs for element, optionally filtered by predicate
        """
        if element not in self.beliefs:
            return []
        
        if predicate is None:
            return self.beliefs[element].copy()
        else:
            return [b for b in self.beliefs[element] if b.predicate == predicate]
    
    def get_belief_value(self, element: OSLElement, predicate: str) -> Optional[Any]:
        """
        Get belief value for specific predicate at element
        If multiple beliefs exist, returns the one with highest confidence
        """
        beliefs = self.get_beliefs(element, predicate)
        if not beliefs:
            return None
        
        # Return value of belief with highest confidence
        best_belief = max(beliefs, key=lambda b: b.confidence)
        return best_belief.value
    
    def get_belief_confidence(self, element: OSLElement, predicate: str) -> float:
        """
        Get belief confidence for specific predicate at element
        """
        beliefs = self.get_beliefs(element, predicate)
        if not beliefs:
            return 0.0
        
        # Return confidence of belief with highest confidence
        best_belief = max(beliefs, key=lambda b: b.confidence)
        return best_belief.confidence
    
    def has_belief(self, element: OSLElement, predicate: str) -> bool:
        """
        Check if element has any belief about predicate
        """
        return len(self.get_beliefs(element, predicate)) > 0
    
    def remove_belief(self, element: OSLElement, predicate: str, value: Any = None) -> bool:
        """
        Remove belief(s) from element
        If value is specified, only remove beliefs with that value
        Returns True if any beliefs were removed
        """
        if element not in self.beliefs:
            return False
        
        original_count = len(self.beliefs[element])
        
        if value is None:
            # Remove all beliefs with this predicate
            self.beliefs[element] = [b for b in self.beliefs[element] if b.predicate != predicate]
            self.predicate_index[predicate][element] = []
        else:
            # Remove beliefs with specific predicate and value
            self.beliefs[element] = [b for b in self.beliefs[element] 
                                   if not (b.predicate == predicate and b.value == value)]
            self.predicate_index[predicate][element] = [b for b in self.predicate_index[predicate][element]
                                                       if b.value != value]
        
        return len(self.beliefs[element]) < original_count
    
    def get_all_predicates(self) -> Set[str]:
        """
        Get all predicates that have beliefs in the belief base
        """
        predicates = set()
        for element_beliefs in self.beliefs.values():
            for belief in element_beliefs:
                predicates.add(belief.predicate)
        return predicates
    
    def get_elements_with_predicate(self, predicate: str) -> Set[OSLElement]:
        """
        Get all elements that have beliefs about the given predicate
        """
        return set(self.predicate_index[predicate].keys())
    
    def propagate_belief_up(self, element: OSLElement, predicate: str, 
                           decay_factor: float = 0.9) -> int:
        """
        Propagate belief upward through lattice cone
        Real belief propagation with confidence decay
        Returns number of elements affected
        """
        if not self.has_belief(element, predicate):
            return 0
        
        source_belief = max(self.get_beliefs(element, predicate), key=lambda b: b.confidence)
        upper_cone = self.lattice.get_cone_up(element)
        affected_count = 0
        
        for upper_element in upper_cone:
            if upper_element == element:
                continue
            
            # Calculate propagated confidence with decay
            propagated_confidence = source_belief.confidence * decay_factor
            
            if propagated_confidence > 0.1:  # Only propagate if confidence is meaningful
                # Check if we should update existing belief
                existing_beliefs = self.get_beliefs(upper_element, predicate)
                should_add = True
                
                for existing in existing_beliefs:
                    if existing.value == source_belief.value:
                        # Same value, update if higher confidence
                        if propagated_confidence > existing.confidence:
                            self.remove_belief(upper_element, predicate, existing.value)
                        else:
                            should_add = False
                        break
                    elif existing.is_contradictory(Belief(predicate, source_belief.value, propagated_confidence)):
                        # Contradictory value, only add if much higher confidence
                        if propagated_confidence > existing.confidence * 1.5:
                            self.remove_belief(upper_element, predicate, existing.value)
                        else:
                            should_add = False
                        break
                
                if should_add:
                    self.add_belief(upper_element, predicate, source_belief.value, 
                                  propagated_confidence, f"propagated_from_{element}")
                    affected_count += 1
        
        return affected_count
    
    def propagate_belief_down(self, element: OSLElement, predicate: str, 
                             decay_factor: float = 0.9) -> int:
        """
        Propagate belief downward through lattice cone
        Real belief propagation with confidence decay
        Returns number of elements affected
        """
        if not self.has_belief(element, predicate):
            return 0
        
        source_belief = max(self.get_beliefs(element, predicate), key=lambda b: b.confidence)
        lower_cone = self.lattice.get_cone_down(element)
        affected_count = 0
        
        for lower_element in lower_cone:
            if lower_element == element:
                continue
            
            # Calculate propagated confidence with decay
            propagated_confidence = source_belief.confidence * decay_factor
            
            if propagated_confidence > 0.1:  # Only propagate if confidence is meaningful
                # Check if we should update existing belief
                existing_beliefs = self.get_beliefs(lower_element, predicate)
                should_add = True
                
                for existing in existing_beliefs:
                    if existing.value == source_belief.value:
                        # Same value, update if higher confidence
                        if propagated_confidence > existing.confidence:
                            self.remove_belief(lower_element, predicate, existing.value)
                        else:
                            should_add = False
                        break
                    elif existing.is_contradictory(Belief(predicate, source_belief.value, propagated_confidence)):
                        # Contradictory value, only add if much higher confidence
                        if propagated_confidence > existing.confidence * 1.5:
                            self.remove_belief(lower_element, predicate, existing.value)
                        else:
                            should_add = False
                        break
                
                if should_add:
                    self.add_belief(lower_element, predicate, source_belief.value, 
                                  propagated_confidence, f"propagated_from_{element}")
                    affected_count += 1
        
        return affected_count
    
    def detect_contradictions(self) -> List[Tuple[OSLElement, Belief, OSLElement, Belief]]:
        """
        Detect all contradictions in the belief base
        Real contradiction detection algorithm
        """
        contradictions = []
        
        # Check contradictions within same element
        for element, element_beliefs in self.beliefs.items():
            for i, belief1 in enumerate(element_beliefs):
                for j, belief2 in enumerate(element_beliefs[i+1:], i+1):
                    if belief1.is_contradictory(belief2):
                        contradictions.append((element, belief1, element, belief2))
        
        # Check contradictions across related elements in lattice
        for predicate in self.get_all_predicates():
            elements_with_predicate = self.get_elements_with_predicate(predicate)
            
            for element1 in elements_with_predicate:
                beliefs1 = self.get_beliefs(element1, predicate)
                
                # Check against comparable elements
                for element2 in elements_with_predicate:
                    if element1 != element2 and element1.is_comparable(element2):
                        beliefs2 = self.get_beliefs(element2, predicate)
                        
                        for belief1 in beliefs1:
                            for belief2 in beliefs2:
                                if belief1.is_contradictory(belief2):
                                    contradictions.append((element1, belief1, element2, belief2))
        
        return contradictions
    
    def resolve_contradictions(self, method: str = 'confidence') -> int:
        """
        Resolve contradictions in belief base using specified method
        Real contradiction resolution algorithm
        Returns number of contradictions resolved
        """
        contradictions = self.detect_contradictions()
        resolved_count = 0
        
        for elem1, belief1, elem2, belief2 in contradictions:
            if method == 'confidence':
                # Keep belief with higher confidence
                if belief1.confidence > belief2.confidence:
                    self.remove_belief(elem2, belief2.predicate, belief2.value)
                elif belief2.confidence > belief1.confidence:
                    self.remove_belief(elem1, belief1.predicate, belief1.value)
                # If equal confidence, keep both (unresolved)
                
            elif method == 'source_priority':
                # Prioritize beliefs from certain sources
                priority_sources = ['sensor', 'expert', 'user']
                source1_priority = priority_sources.index(belief1.source) if belief1.source in priority_sources else len(priority_sources)
                source2_priority = priority_sources.index(belief2.source) if belief2.source in priority_sources else len(priority_sources)
                
                if source1_priority < source2_priority:
                    self.remove_belief(elem2, belief2.predicate, belief2.value)
                elif source2_priority < source1_priority:
                    self.remove_belief(elem1, belief1.predicate, belief1.value)
                
            elif method == 'temporal':
                # Keep more recent belief (if timestamps available)
                if belief1.timestamp and belief2.timestamp:
                    if belief1.timestamp > belief2.timestamp:
                        self.remove_belief(elem2, belief2.predicate, belief2.value)
                    elif belief2.timestamp > belief1.timestamp:
                        self.remove_belief(elem1, belief1.predicate, belief1.value)
            
            resolved_count += 1
        
        return resolved_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the belief base
        """
        total_beliefs = sum(len(beliefs) for beliefs in self.beliefs.values())
        total_elements_with_beliefs = len([elem for elem, beliefs in self.beliefs.items() if beliefs])
        
        # Confidence statistics
        all_confidences = []
        for element_beliefs in self.beliefs.values():
            for belief in element_beliefs:
                all_confidences.append(belief.confidence)
        
        confidence_stats = {}
        if all_confidences:
            confidence_stats = {
                'mean': np.mean(all_confidences),
                'std': np.std(all_confidences),
                'min': np.min(all_confidences),
                'max': np.max(all_confidences),
                'median': np.median(all_confidences)
            }
        
        # Predicate statistics
        predicate_counts = defaultdict(int)
        for element_beliefs in self.beliefs.values():
            for belief in element_beliefs:
                predicate_counts[belief.predicate] += 1
        
        return {
            'total_beliefs': total_beliefs,
            'total_elements_with_beliefs': total_elements_with_beliefs,
            'total_predicates': len(self.get_all_predicates()),
            'confidence_statistics': confidence_stats,
            'predicate_distribution': dict(predicate_counts),
            'contradiction_count': len(self.detect_contradictions()),
            'lattice_size': self.lattice.size()
        }
    
    def size(self) -> int:
        """Get total number of beliefs in the belief base"""
        return sum(len(beliefs) for beliefs in self.beliefs.values())
    
    def clear(self):
        """Clear all beliefs from the belief base"""
        self.beliefs.clear()
        self.predicate_index.clear()
        self.contradictions.clear()

