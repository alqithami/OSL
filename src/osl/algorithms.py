"""
Core algorithms for the OSL framework.

This module implements the Relativized Belief Propagation (RBP) and 
Minimal Contradiction Decomposition (MCC) algorithms as described in the paper.
"""

import time
from typing import List, Set, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

from .lattice import OSLattice
from .belief_base import BeliefBase, BeliefRecord


@dataclass
class PropagationResult:
    """Result of an RBP propagation operation."""
    affected_elements: Set[Tuple[str, str]]
    processing_time: float
    contradictions_detected: List[Tuple[str, str]]
    records_updated: int


@dataclass  
class MinimalContradictionComponent:
    """A minimal contradiction component (MCC)."""
    root_element: Tuple[str, str]  # Element where contradiction first appears
    proposition: str  # The contradictory proposition
    supporting_records: List[BeliefRecord]  # Records supporting the proposition
    contradicting_records: List[BeliefRecord]  # Records contradicting the proposition
    
    @property
    def all_records(self) -> List[BeliefRecord]:
        """All records involved in this MCC."""
        return self.supporting_records + self.contradicting_records


class RBPAlgorithm:
    """
    Relativized Belief Propagation algorithm.
    
    Implements incremental belief updates with complexity O(d_e + c_e) where
    d_e and c_e are the number of descendants and ancestors of element e.
    """
    
    def __init__(self, belief_base: BeliefBase):
        """
        Initialize the RBP algorithm.
        
        Args:
            belief_base: The belief base to operate on
        """
        self.belief_base = belief_base
        self.lattice = belief_base.lattice
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.propagation_stats = {
            'total_propagations': 0,
            'total_time': 0.0,
            'max_affected_elements': 0,
            'avg_affected_elements': 0.0
        }
    
    def propagate(self, record: BeliefRecord, 
                  attenuation_factor: float = 0.9) -> PropagationResult:
        """
        Perform RBP propagation for a new belief record.
        
        Args:
            record: The belief record to propagate
            attenuation_factor: Factor for attenuating belief strength upward
            
        Returns:
            PropagationResult with details of the propagation
        """
        start_time = time.time()
        
        element = record.element
        proposition = record.proposition
        
        # Get ancestor and descendant cones
        ancestors = self.lattice.ancestors(element)
        descendants = self.lattice.descendants(element)
        
        affected_elements = set()
        contradictions_detected = []
        records_updated = 0
        
        # Upward propagation to ancestors
        for ancestor in ancestors:
            if ancestor != element:
                # Create attenuated record for ancestor
                attenuated_weight = record.weight * (attenuation_factor ** 
                    self._distance(element, ancestor))
                
                if attenuated_weight >= 0.01:  # Minimum threshold for propagation
                    propagated_record = BeliefRecord(
                        proposition=proposition,
                        element=ancestor,
                        weight=attenuated_weight,
                        timestamp=record.timestamp,
                        source=f"propagated_from_{element}"
                    )
                    
                    # Add to belief base without triggering another propagation
                    self._add_record_direct(propagated_record)
                    affected_elements.add(ancestor)
                    records_updated += 1
                    
                    # Check for contradictions
                    if self._check_local_contradiction(proposition, ancestor):
                        contradictions_detected.append((proposition, ancestor))
        
        # Downward attenuation (optional, for belief revision)
        for descendant in descendants:
            if descendant != element:
                # Potentially reduce strength of contradictory beliefs
                self._attenuate_contradictory_beliefs(proposition, descendant, 0.8)
        
        processing_time = time.time() - start_time
        
        # Update statistics
        self.propagation_stats['total_propagations'] += 1
        self.propagation_stats['total_time'] += processing_time
        self.propagation_stats['max_affected_elements'] = max(
            self.propagation_stats['max_affected_elements'],
            len(affected_elements)
        )
        
        # Update running average
        n = self.propagation_stats['total_propagations']
        old_avg = self.propagation_stats['avg_affected_elements']
        self.propagation_stats['avg_affected_elements'] = (
            (old_avg * (n - 1) + len(affected_elements)) / n
        )
        
        result = PropagationResult(
            affected_elements=affected_elements,
            processing_time=processing_time,
            contradictions_detected=contradictions_detected,
            records_updated=records_updated
        )
        
        self.logger.debug(f"RBP propagation completed: {len(affected_elements)} elements "
                         f"affected in {processing_time:.4f}s")
        
        return result
    
    def _distance(self, e1: Tuple[str, str], e2: Tuple[str, str]) -> int:
        """
        Compute lattice distance between two elements.
        
        This is a simplified distance metric based on the number of steps
        in the lattice ordering. In practice, this could be more sophisticated.
        """
        if e1 == e2:
            return 0
        
        # Simple heuristic: count differences in observer and situation
        o1, s1 = e1
        o2, s2 = e2
        
        distance = 0
        if o1 != o2:
            distance += 1
        if s1 != s2:
            distance += 1
        
        return distance
    
    def _add_record_direct(self, record: BeliefRecord):
        """Add a record directly without triggering propagation."""
        prop = record.proposition
        elem = record.element
        
        self.belief_base.beliefs[prop][elem].append(record)
        self.belief_base.element_index[elem].add(prop)
        self.belief_base.stats['total_beliefs'] += 1
    
    def _check_local_contradiction(self, proposition: str, element: Tuple[str, str]) -> bool:
        """Check if a proposition creates a contradiction at the given element."""
        if proposition.startswith("¬"):
            positive_prop = proposition[1:]
            negative_prop = proposition
        else:
            positive_prop = proposition
            negative_prop = f"¬{proposition}"
        
        pos_strength = self.belief_base.query(positive_prop, element)
        neg_strength = self.belief_base.query(negative_prop, element)
        
        threshold = self.belief_base.threshold
        return pos_strength >= threshold and neg_strength >= threshold
    
    def _attenuate_contradictory_beliefs(self, proposition: str, element: Tuple[str, str], 
                                       factor: float):
        """Attenuate beliefs that contradict the given proposition."""
        if proposition.startswith("¬"):
            contradictory_prop = proposition[1:]
        else:
            contradictory_prop = f"¬{proposition}"
        
        # Find and attenuate contradictory records
        if contradictory_prop in self.belief_base.beliefs:
            element_records = self.belief_base.beliefs[contradictory_prop].get(element, [])
            for record in element_records:
                record.weight *= factor
    
    def get_complexity_estimate(self, element: Tuple[str, str]) -> Dict[str, int]:
        """
        Get complexity estimate for propagating from the given element.
        
        Returns:
            Dictionary with 'ancestors', 'descendants', and 'total' counts
        """
        ancestors = len(self.lattice.ancestors(element))
        descendants = len(self.lattice.descendants(element))
        
        return {
            'ancestors': ancestors,
            'descendants': descendants,
            'total': ancestors + descendants,
            'theoretical_complexity': f"O({ancestors + descendants})"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RBP algorithm statistics."""
        return dict(self.propagation_stats)


class MCCAlgorithm:
    """
    Minimal Contradiction Decomposition algorithm.
    
    Implements detection and extraction of minimal contradiction components
    in O(|B| log |B|) time as claimed in the paper.
    """
    
    def __init__(self, belief_base: BeliefBase):
        """
        Initialize the MCC algorithm.
        
        Args:
            belief_base: The belief base to analyze
        """
        self.belief_base = belief_base
        self.lattice = belief_base.lattice
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.mcc_stats = {
            'total_extractions': 0,
            'total_time': 0.0,
            'max_mccs_found': 0,
            'avg_mccs_found': 0.0
        }
    
    def extract_mccs(self) -> List[MinimalContradictionComponent]:
        """
        Extract all minimal contradiction components from the belief base.
        
        Returns:
            List of MinimalContradictionComponent objects
        """
        start_time = time.time()
        
        mccs = []
        processed_contradictions = set()
        
        # Get all belief records and sort by element for efficient processing
        all_records = []
        for prop, element_dict in self.belief_base.beliefs.items():
            for element, records in element_dict.items():
                all_records.extend(records)
        
        # Sort records by element (lexicographic order)
        all_records.sort(key=lambda r: r.element)
        
        # Group records by proposition
        prop_records = defaultdict(list)
        for record in all_records:
            prop_records[record.proposition].append(record)
        
        # Find contradictory proposition pairs
        propositions = set(prop_records.keys())
        for prop in propositions:
            if prop in processed_contradictions:
                continue
                
            # Find negation
            if prop.startswith("¬"):
                neg_prop = prop[1:]
                pos_prop = neg_prop
            else:
                pos_prop = prop
                neg_prop = f"¬{prop}"
            
            if neg_prop in propositions:
                # Found a contradictory pair
                mcc = self._find_mcc_for_proposition_pair(pos_prop, neg_prop)
                if mcc:
                    mccs.append(mcc)
                
                processed_contradictions.add(pos_prop)
                processed_contradictions.add(neg_prop)
        
        processing_time = time.time() - start_time
        
        # Update statistics
        self.mcc_stats['total_extractions'] += 1
        self.mcc_stats['total_time'] += processing_time
        self.mcc_stats['max_mccs_found'] = max(
            self.mcc_stats['max_mccs_found'],
            len(mccs)
        )
        
        # Update running average
        n = self.mcc_stats['total_extractions']
        old_avg = self.mcc_stats['avg_mccs_found']
        self.mcc_stats['avg_mccs_found'] = (
            (old_avg * (n - 1) + len(mccs)) / n
        )
        
        self.logger.debug(f"MCC extraction completed: {len(mccs)} MCCs found "
                         f"in {processing_time:.4f}s")
        
        return mccs
    
    def _find_mcc_for_proposition_pair(self, pos_prop: str, neg_prop: str) -> Optional[MinimalContradictionComponent]:
        """
        Find the MCC for a specific contradictory proposition pair.
        
        Args:
            pos_prop: The positive proposition
            neg_prop: The negative proposition
            
        Returns:
            MinimalContradictionComponent if found, None otherwise
        """
        # Get all records for both propositions
        pos_records = []
        neg_records = []
        
        if pos_prop in self.belief_base.beliefs:
            for element, records in self.belief_base.beliefs[pos_prop].items():
                pos_records.extend(records)
        
        if neg_prop in self.belief_base.beliefs:
            for element, records in self.belief_base.beliefs[neg_prop].items():
                neg_records.extend(records)
        
        if not pos_records or not neg_records:
            return None
        
        # Find the minimal element where contradiction occurs
        threshold = self.belief_base.threshold
        
        # Check each lattice element bottom-up
        contradiction_elements = []
        
        for element in self.lattice.elements:
            pos_strength = self.belief_base.query(pos_prop, element)
            neg_strength = self.belief_base.query(neg_prop, element)
            
            if pos_strength >= threshold and neg_strength >= threshold:
                contradiction_elements.append(element)
        
        if not contradiction_elements:
            return None
        
        # Find the minimal contradiction element
        # (element with no contradictory descendants)
        minimal_elements = []
        for elem in contradiction_elements:
            is_minimal = True
            descendants = self.lattice.descendants(elem)
            
            for desc in descendants:
                if desc != elem and desc in contradiction_elements:
                    is_minimal = False
                    break
            
            if is_minimal:
                minimal_elements.append(elem)
        
        if not minimal_elements:
            return None
        
        # Take the first minimal element (there should be only one for a proper MCC)
        root_element = minimal_elements[0]
        
        # Collect the records that contribute to this MCC
        contributing_pos_records = []
        contributing_neg_records = []
        
        root_descendants = self.lattice.descendants(root_element)
        
        for record in pos_records:
            if record.element in root_descendants and record.weight >= threshold:
                contributing_pos_records.append(record)
        
        for record in neg_records:
            if record.element in root_descendants and record.weight >= threshold:
                contributing_neg_records.append(record)
        
        return MinimalContradictionComponent(
            root_element=root_element,
            proposition=pos_prop,
            supporting_records=contributing_pos_records,
            contradicting_records=contributing_neg_records
        )
    
    def get_complexity_estimate(self) -> Dict[str, Any]:
        """
        Get complexity estimate for MCC extraction.
        
        Returns:
            Dictionary with complexity information
        """
        total_beliefs = len(self.belief_base)
        lattice_size = self.lattice.size()
        
        return {
            'total_beliefs': total_beliefs,
            'lattice_size': lattice_size,
            'theoretical_complexity': f"O({total_beliefs} * log({total_beliefs}))",
            'practical_complexity': f"O({total_beliefs} * {lattice_size})"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get MCC algorithm statistics."""
        return dict(self.mcc_stats)

