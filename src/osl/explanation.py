"""
Explanation generation module for the OSL framework.

This module provides capabilities for generating perspective-aware
explanations tailored to different audiences.
"""

from typing import Dict, List, Tuple, Any, Optional
from .lattice import OSLattice
from .belief_base import BeliefBase


class ExplanationGenerator:
    """
    Generates perspective-aware explanations using the OSL framework.
    
    This class can create explanations that are tailored to the recipient's
    perspective and knowledge state.
    """
    
    def __init__(self, belief_base: BeliefBase):
        """
        Initialize the explanation generator.
        
        Args:
            belief_base: The belief base to generate explanations from
        """
        self.belief_base = belief_base
        self.lattice = belief_base.lattice
    
    def generate_explanation(self, explainer: str, recipient: str, 
                           situation: str, topic: str) -> Dict[str, Any]:
        """
        Generate an explanation tailored to the recipient's perspective.
        
        Args:
            explainer: The observer providing the explanation
            recipient: The observer receiving the explanation
            situation: The current situation
            topic: The topic to explain
            
        Returns:
            Dictionary containing the explanation and metadata
        """
        explainer_elem = (explainer, situation)
        recipient_elem = (recipient, situation)
        
        # Get beliefs of both parties
        explainer_beliefs = self.belief_base.get_beliefs_at(explainer_elem)
        recipient_beliefs = self.belief_base.get_beliefs_at(recipient_elem)
        
        # Find the knowledge gap
        knowledge_gap = self._identify_knowledge_gap(
            explainer_beliefs, recipient_beliefs, topic
        )
        
        # Generate explanation based on the gap
        explanation_text = self._generate_explanation_text(
            knowledge_gap, topic, explainer, recipient
        )
        
        return {
            'explanation': explanation_text,
            'knowledge_gap': knowledge_gap,
            'explainer': explainer,
            'recipient': recipient,
            'situation': situation,
            'topic': topic,
            'confidence': self._calculate_explanation_confidence(knowledge_gap)
        }
    
    def _identify_knowledge_gap(self, explainer_beliefs: Dict[str, float],
                               recipient_beliefs: Dict[str, float],
                               topic: str) -> Dict[str, Any]:
        """Identify what the recipient doesn't know that the explainer does."""
        gap = {
            'missing_knowledge': [],
            'incorrect_beliefs': [],
            'shared_knowledge': []
        }
        
        # Find topic-related propositions
        topic_props = [prop for prop in explainer_beliefs.keys() 
                      if topic.lower() in prop.lower()]
        
        for prop in topic_props:
            explainer_val = explainer_beliefs.get(prop, 0.0)
            recipient_val = recipient_beliefs.get(prop, 0.0)
            
            if explainer_val >= self.belief_base.threshold:
                if recipient_val < self.belief_base.threshold:
                    gap['missing_knowledge'].append(prop)
                elif abs(explainer_val - recipient_val) > 0.3:
                    gap['incorrect_beliefs'].append((prop, recipient_val, explainer_val))
                else:
                    gap['shared_knowledge'].append(prop)
        
        return gap
    
    def _generate_explanation_text(self, knowledge_gap: Dict[str, Any],
                                 topic: str, explainer: str, 
                                 recipient: str) -> str:
        """Generate natural language explanation text."""
        explanation_parts = []
        
        # Address missing knowledge
        if knowledge_gap['missing_knowledge']:
            explanation_parts.append(
                f"You may not be aware that {', '.join(knowledge_gap['missing_knowledge'])}."
            )
        
        # Address incorrect beliefs
        if knowledge_gap['incorrect_beliefs']:
            for prop, recipient_val, explainer_val in knowledge_gap['incorrect_beliefs']:
                explanation_parts.append(
                    f"Regarding {prop}, I believe it's {explainer_val:.2f} likely, "
                    f"while you might think it's {recipient_val:.2f} likely."
                )
        
        # Acknowledge shared knowledge
        if knowledge_gap['shared_knowledge']:
            explanation_parts.append(
                f"We both understand that {', '.join(knowledge_gap['shared_knowledge'])}."
            )
        
        if not explanation_parts:
            explanation_parts.append(f"We seem to have similar understanding of {topic}.")
        
        return " ".join(explanation_parts)
    
    def _calculate_explanation_confidence(self, knowledge_gap: Dict[str, Any]) -> float:
        """Calculate confidence in the explanation quality."""
        total_items = (len(knowledge_gap['missing_knowledge']) + 
                      len(knowledge_gap['incorrect_beliefs']) + 
                      len(knowledge_gap['shared_knowledge']))
        
        if total_items == 0:
            return 0.5  # Neutral confidence when no information
        
        # Higher confidence when there's more shared knowledge
        shared_ratio = len(knowledge_gap['shared_knowledge']) / total_items
        return 0.3 + 0.7 * shared_ratio  # Scale between 0.3 and 1.0

