"""
Belief base management for the OSL framework.

This module implements storage and querying of perspective-indexed beliefs
within the Observer-Situation Lattice structure.
"""

from typing import Dict, List, Tuple, Set, Any, Optional, Union
from dataclasses import dataclass
from collections import defaultdict
import time
import logging

from .lattice import OSLattice


@dataclass
class BeliefRecord:
    """A single belief record in the OSL framework."""
    proposition: str
    element: Tuple[str, str]  # (observer, situation)
    weight: float
    timestamp: float
    source: Optional[str] = None
    
    def __post_init__(self):
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be in [0,1], got {self.weight}")


class BeliefBase:
    """
    Manages beliefs indexed by Observer-Situation Lattice elements.
    
    This class provides storage, querying, and update operations for beliefs
    that are tagged with specific (observer, situation) pairs.
    """
    
    def __init__(self, lattice: OSLattice, credibility_threshold: float = 0.5):
        """
        Initialize the belief base.
        
        Args:
            lattice: The underlying OSL lattice structure
            credibility_threshold: Minimum weight for belief acceptance
        """
        self.lattice = lattice
        self.threshold = credibility_threshold
        
        # Storage: proposition -> element -> list of records
        self.beliefs: Dict[str, Dict[Tuple[str, str], List[BeliefRecord]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Reverse index: element -> set of propositions
        self.element_index: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        
        # Contradiction tracking
        self.contradictions: Set[Tuple[str, str]] = set()
        
        # Statistics
        self.stats = {
            'total_beliefs': 0,
            'updates': 0,
            'queries': 0,
            'contradictions_detected': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    def add_belief(self, proposition: str, element: Tuple[str, str], 
                   weight: float, source: Optional[str] = None) -> BeliefRecord:
        """
        Add a new belief record to the base.
        
        Args:
            proposition: The proposition being asserted (e.g., "spill_detected")
            element: The (observer, situation) pair
            weight: Credibility weight in [0,1]
            source: Optional source identifier
            
        Returns:
            The created BeliefRecord
            
        Raises:
            ValueError: If element is not in the lattice
        """
        if element not in self.lattice.element_set:
            raise ValueError(f"Element {element} not in lattice")
        
        record = BeliefRecord(
            proposition=proposition,
            element=element,
            weight=weight,
            timestamp=time.time(),
            source=source
        )
        
        # Store the record
        self.beliefs[proposition][element].append(record)
        self.element_index[element].add(proposition)
        
        # Update statistics
        self.stats['total_beliefs'] += 1
        self.stats['updates'] += 1
        
        # Check for contradictions
        self._check_contradiction(proposition, element)
        
        self.logger.debug(f"Added belief: {proposition} at {element} with weight {weight}")
        
        return record
    
    def query(self, proposition: str, element: Tuple[str, str], 
              aggregation: str = 'max') -> float:
        """
        Query the belief strength for a proposition at a given element.
        
        Uses upward closure: belief at element e is supported by all records
        at elements e' ≼ e in the lattice.
        
        Args:
            proposition: The proposition to query
            element: The (observer, situation) pair
            aggregation: How to combine multiple records ('max', 'mean', 'weighted_mean')
            
        Returns:
            Aggregated belief strength in [0,1]
        """
        if element not in self.lattice.element_set:
            raise ValueError(f"Element {element} not in lattice")
        
        self.stats['queries'] += 1
        
        # Collect all supporting records from descendants
        supporting_records = []
        descendants = self.lattice.descendants(element)
        
        for desc_elem in descendants:
            if proposition in self.beliefs:
                records = self.beliefs[proposition].get(desc_elem, [])
                supporting_records.extend(records)
        
        if not supporting_records:
            return 0.0
        
        # Aggregate the weights
        if aggregation == 'max':
            return max(record.weight for record in supporting_records)
        elif aggregation == 'mean':
            return sum(record.weight for record in supporting_records) / len(supporting_records)
        elif aggregation == 'weighted_mean':
            # Weight by recency (more recent = higher weight)
            current_time = time.time()
            total_weight = 0.0
            total_mass = 0.0
            
            for record in supporting_records:
                age = current_time - record.timestamp
                time_weight = max(0.1, 1.0 / (1.0 + age / 3600.0))  # Decay over hours
                total_weight += record.weight * time_weight
                total_mass += time_weight
            
            return total_weight / total_mass if total_mass > 0 else 0.0
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
    
    def believes(self, element: Tuple[str, str], proposition: str) -> bool:
        """
        Check if the given element believes the proposition above threshold.
        
        Args:
            element: The (observer, situation) pair
            proposition: The proposition to check
            
        Returns:
            True if belief strength >= threshold
        """
        strength = self.query(proposition, element)
        return strength >= self.threshold
    
    def get_beliefs_at(self, element: Tuple[str, str]) -> Dict[str, float]:
        """
        Get all beliefs held at a specific element.
        
        Args:
            element: The (observer, situation) pair
            
        Returns:
            Dictionary mapping propositions to belief strengths
        """
        beliefs = {}
        propositions = self.element_index.get(element, set())
        
        # Also check ancestors for inherited beliefs
        ancestors = self.lattice.ancestors(element)
        for ancestor in ancestors:
            propositions.update(self.element_index.get(ancestor, set()))
        
        for prop in propositions:
            strength = self.query(prop, element)
            if strength > 0:
                beliefs[prop] = strength
        
        return beliefs
    
    def get_contradictions(self) -> List[Tuple[str, Tuple[str, str]]]:
        """
        Get all current contradictions in the belief base.
        
        Returns:
            List of (proposition, element) pairs where contradictions exist
        """
        contradictions = []
        
        for element in self.contradictions:
            # Find which propositions are contradictory at this element
            element_beliefs = self.get_beliefs_at(element)
            
            for prop in element_beliefs:
                neg_prop = f"¬{prop}" if not prop.startswith("¬") else prop[1:]
                
                if prop in element_beliefs and neg_prop in element_beliefs:
                    if (element_beliefs[prop] >= self.threshold and 
                        element_beliefs[neg_prop] >= self.threshold):
                        contradictions.append((prop, element))
        
        return contradictions
    
    def _check_contradiction(self, proposition: str, element: Tuple[str, str]):
        """Check if adding this belief creates a contradiction."""
        # Check for negation
        if proposition.startswith("¬"):
            positive_prop = proposition[1:]
            negative_prop = proposition
        else:
            positive_prop = proposition
            negative_prop = f"¬{proposition}"
        
        # Check all ancestors for contradictory beliefs
        ancestors = self.lattice.ancestors(element)
        
        for ancestor in ancestors:
            pos_strength = self.query(positive_prop, ancestor)
            neg_strength = self.query(negative_prop, ancestor)
            
            if pos_strength >= self.threshold and neg_strength >= self.threshold:
                self.contradictions.add(ancestor)
                self.stats['contradictions_detected'] += 1
                self.logger.warning(f"Contradiction detected at {ancestor}: {positive_prop} vs {negative_prop}")
    
    def resolve_contradiction(self, proposition: str, element: Tuple[str, str], 
                            resolution_strategy: str = 'latest') -> bool:
        """
        Attempt to resolve a contradiction using the specified strategy.
        
        Args:
            proposition: The contradictory proposition
            element: The element where contradiction occurs
            resolution_strategy: 'latest', 'highest_weight', 'source_priority'
            
        Returns:
            True if contradiction was resolved
        """
        if proposition.startswith("¬"):
            positive_prop = proposition[1:]
            negative_prop = proposition
        else:
            positive_prop = proposition
            negative_prop = f"¬{proposition}"
        
        # Get all records for both propositions
        pos_records = []
        neg_records = []
        
        descendants = self.lattice.descendants(element)
        for desc_elem in descendants:
            pos_records.extend(self.beliefs[positive_prop].get(desc_elem, []))
            neg_records.extend(self.beliefs[negative_prop].get(desc_elem, []))
        
        if not pos_records or not neg_records:
            return True  # No actual contradiction
        
        # Apply resolution strategy
        if resolution_strategy == 'latest':
            # Keep the most recent records, remove older ones
            all_records = pos_records + neg_records
            all_records.sort(key=lambda r: r.timestamp, reverse=True)
            
            # Keep records from the latest timestamp
            latest_time = all_records[0].timestamp
            keep_records = [r for r in all_records if r.timestamp == latest_time]
            
            # Remove older records
            for record in all_records:
                if record not in keep_records:
                    self._remove_record(record)
        
        elif resolution_strategy == 'highest_weight':
            # Keep records with highest weight
            max_weight = max(max(r.weight for r in pos_records), 
                           max(r.weight for r in neg_records))
            
            # Remove records with lower weight
            for record in pos_records + neg_records:
                if record.weight < max_weight:
                    self._remove_record(record)
        
        # Check if contradiction is resolved
        pos_strength = self.query(positive_prop, element)
        neg_strength = self.query(negative_prop, element)
        
        resolved = not (pos_strength >= self.threshold and neg_strength >= self.threshold)
        
        if resolved:
            self.contradictions.discard(element)
            self.logger.info(f"Resolved contradiction at {element} for {proposition}")
        
        return resolved
    
    def _remove_record(self, record: BeliefRecord):
        """Remove a specific record from the belief base."""
        prop_beliefs = self.beliefs[record.proposition]
        element_records = prop_beliefs[record.element]
        
        if record in element_records:
            element_records.remove(record)
            self.stats['total_beliefs'] -= 1
            
            # Clean up empty structures
            if not element_records:
                del prop_beliefs[record.element]
                self.element_index[record.element].discard(record.proposition)
                
                if not self.element_index[record.element]:
                    del self.element_index[record.element]
            
            if not prop_beliefs:
                del self.beliefs[record.proposition]
    
    def clear(self):
        """Clear all beliefs from the base."""
        self.beliefs.clear()
        self.element_index.clear()
        self.contradictions.clear()
        self.stats = {
            'total_beliefs': 0,
            'updates': 0,
            'queries': 0,
            'contradictions_detected': 0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics about the belief base."""
        return {
            **self.stats,
            'unique_propositions': len(self.beliefs),
            'active_elements': len(self.element_index),
            'contradictions': len(self.contradictions),
            'lattice_size': self.lattice.size()
        }
    
    def __len__(self) -> int:
        """Return the total number of belief records."""
        return self.stats['total_beliefs']
    
    def __str__(self) -> str:
        """String representation of the belief base."""
        return f"BeliefBase({self.stats['total_beliefs']} beliefs, {len(self.contradictions)} contradictions)"

