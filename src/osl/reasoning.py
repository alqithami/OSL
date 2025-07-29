"""
Theory-of-Mind reasoning module for the OSL framework.

This module provides reasoning capabilities for perspective-taking
and false belief scenarios.
"""

from typing import Dict, List, Tuple, Any, Optional
from .lattice import OSLattice
from .belief_base import BeliefBase


class TheoryOfMindReasoner:
    """
    Theory-of-Mind reasoning capabilities for the OSL framework.
    
    This class provides methods for reasoning about what other observers
    believe and predicting their behavior based on their perspective.
    """
    
    def __init__(self, belief_base: BeliefBase):
        """
        Initialize the Theory-of-Mind reasoner.
        
        Args:
            belief_base: The belief base to reason over
        """
        self.belief_base = belief_base
        self.lattice = belief_base.lattice
    
    def predict_behavior(self, observer: str, situation: str, 
                        behavior_rules: Dict[str, str]) -> str:
        """
        Predict an observer's behavior based on their beliefs.
        
        Args:
            observer: The observer whose behavior to predict
            situation: The current situation
            behavior_rules: Mapping from belief patterns to behaviors
            
        Returns:
            Predicted behavior string
        """
        element = (observer, situation)
        beliefs = self.belief_base.get_beliefs_at(element)
        
        # Apply behavior rules based on beliefs
        for pattern, behavior in behavior_rules.items():
            if pattern in beliefs and beliefs[pattern] >= self.belief_base.threshold:
                return behavior
        
        return "unknown"
    
    def compare_perspectives(self, observer1: str, observer2: str, 
                           situation: str) -> Dict[str, Any]:
        """
        Compare the perspectives of two observers in a given situation.
        
        Args:
            observer1: First observer
            observer2: Second observer  
            situation: The situation to compare
            
        Returns:
            Dictionary with comparison results
        """
        elem1 = (observer1, situation)
        elem2 = (observer2, situation)
        
        beliefs1 = self.belief_base.get_beliefs_at(elem1)
        beliefs2 = self.belief_base.get_beliefs_at(elem2)
        
        # Find shared and different beliefs
        all_props = set(beliefs1.keys()) | set(beliefs2.keys())
        
        shared = {}
        different = {}
        
        for prop in all_props:
            val1 = beliefs1.get(prop, 0.0)
            val2 = beliefs2.get(prop, 0.0)
            
            if abs(val1 - val2) < 0.1:  # Similar beliefs
                shared[prop] = (val1, val2)
            else:
                different[prop] = (val1, val2)
        
        return {
            'shared_beliefs': shared,
            'different_beliefs': different,
            'perspective_similarity': len(shared) / len(all_props) if all_props else 1.0
        }
    
    def detect_false_beliefs(self, observer: str, situation: str) -> List[str]:
        """
        Detect propositions where the observer has false beliefs.
        
        Args:
            observer: The observer to check
            situation: The situation context
            
        Returns:
            List of propositions with false beliefs
        """
        # Get the "ground truth" from the most informed observer
        top_element = self.lattice.get_top()
        ground_truth = self.belief_base.get_beliefs_at(top_element)
        
        # Get the observer's beliefs
        observer_element = (observer, situation)
        observer_beliefs = self.belief_base.get_beliefs_at(observer_element)
        
        false_beliefs = []
        
        for prop in ground_truth:
            if prop in observer_beliefs:
                truth_val = ground_truth[prop] >= self.belief_base.threshold
                belief_val = observer_beliefs[prop] >= self.belief_base.threshold
                
                if truth_val != belief_val:
                    false_beliefs.append(prop)
        
        return false_beliefs

