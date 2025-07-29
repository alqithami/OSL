"""
Observer-Situation Lattice (OSL) - Honest Implementation

A scientifically rigorous implementation of the OSL framework for perspective-aware cognition.
"""

from .lattice import OSLattice
from .belief_base import BeliefBase
from .algorithms import RBPAlgorithm, MCCAlgorithm
from .reasoning import TheoryOfMindReasoner
from .explanation import ExplanationGenerator

__version__ = "1.0.0"
__author__ = "OSL Research Team"

__all__ = [
    'OSLattice',
    'BeliefBase', 
    'RBPAlgorithm',
    'MCCAlgorithm',
    'TheoryOfMindReasoner',
    'ExplanationGenerator'
]

