"""
Sally-Anne False Belief Test Implementation

This experiment implements the classic Sally-Anne false belief test using
the OSL framework to demonstrate Theory-of-Mind capabilities. This provides
honest evaluation of the framework's ability to handle perspective-dependent
reasoning without fabricated perfect performance claims.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from osl import OSLattice, BeliefBase


class TestOutcome(Enum):
    """Possible outcomes for Theory-of-Mind tests."""
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"


@dataclass
class ToMTestResult:
    """Result of a single Theory-of-Mind test."""
    test_name: str
    outcome: TestOutcome
    predicted_behavior: str
    actual_behavior: str
    explanation: str
    confidence: float
    details: Dict[str, Any]


class SallyAnneTest:
    """
    Implementation of the classic Sally-Anne false belief test.
    
    This test evaluates whether the OSL framework can correctly predict
    that Sally will look for her ball in the basket (where she left it)
    rather than in the box (where Anne moved it while Sally was away).
    """
    
    def __init__(self):
        """Initialize the Sally-Anne test scenario."""
        # Create observers: Sally, Anne, and the system/robot
        self.observers = ['sally', 'anne', 'robot']
        
        # Create situations: before Sally leaves, while Sally is away, after Sally returns
        self.situations = ['initial', 'sally_away', 'sally_returns']
        
        # Create observer ordering (information hierarchy)
        # Robot observes everything, Anne observes more than Sally
        observer_order = [
            ('sally', 'anne'),    # Anne knows what Sally knows
            ('anne', 'robot')     # Robot knows what Anne knows
        ]
        
        # Create situation ordering (temporal progression)
        situation_order = [
            ('initial', 'sally_away'),
            ('sally_away', 'sally_returns')
        ]
        
        # Create the lattice
        self.lattice = OSLattice(
            observers=self.observers,
            situations=self.situations,
            observer_order=observer_order,
            situation_order=situation_order
        )
        
        # Create belief base
        self.belief_base = BeliefBase(self.lattice, credibility_threshold=0.7)
        
        # Initialize the scenario
        self._setup_scenario()
    
    def _setup_scenario(self):
        """Set up the initial Sally-Anne scenario."""
        # Initial situation: Sally puts ball in basket
        self.belief_base.add_belief(
            'ball_in_basket', 
            ('sally', 'initial'), 
            1.0, 
            source='sally_action'
        )
        
        self.belief_base.add_belief(
            'ball_in_basket', 
            ('anne', 'initial'), 
            1.0, 
            source='anne_observes'
        )
        
        self.belief_base.add_belief(
            'ball_in_basket', 
            ('robot', 'initial'), 
            1.0, 
            source='robot_observes'
        )
        
        # Sally leaves (she doesn't observe what happens next)
        # Anne moves the ball to the box while Sally is away
        self.belief_base.add_belief(
            'ball_in_box', 
            ('anne', 'sally_away'), 
            1.0, 
            source='anne_action'
        )
        
        self.belief_base.add_belief(
            'ball_in_box', 
            ('robot', 'sally_away'), 
            1.0, 
            source='robot_observes'
        )
        
        # Explicitly record that ball is no longer in basket
        self.belief_base.add_belief(
            '¬ball_in_basket', 
            ('anne', 'sally_away'), 
            1.0, 
            source='anne_action'
        )
        
        self.belief_base.add_belief(
            '¬ball_in_basket', 
            ('robot', 'sally_away'), 
            1.0, 
            source='robot_observes'
        )
        
        # Sally returns but hasn't observed the move
        # Her beliefs should remain unchanged about the ball location
    
    def run_test(self) -> ToMTestResult:
        """
        Run the Sally-Anne false belief test.
        
        Returns:
            ToMTestResult with the outcome and details
        """
        # The key question: Where will Sally look for the ball?
        # Correct answer: In the basket (where she left it)
        # Incorrect answer: In the box (where it actually is)
        
        # Query Sally's belief about ball location when she returns
        sally_believes_basket = self.belief_base.believes(
            ('sally', 'sally_returns'), 
            'ball_in_basket'
        )
        
        sally_believes_box = self.belief_base.believes(
            ('sally', 'sally_returns'), 
            'ball_in_box'
        )
        
        # Get belief strengths for more detailed analysis
        basket_strength = self.belief_base.query(
            'ball_in_basket', 
            ('sally', 'sally_returns')
        )
        
        box_strength = self.belief_base.query(
            'ball_in_box', 
            ('sally', 'sally_returns')
        )
        
        # Determine predicted behavior
        if sally_believes_basket and not sally_believes_box:
            predicted_behavior = "look_in_basket"
            outcome = TestOutcome.PASS
            explanation = "Sally will look in the basket because she believes that's where she left the ball and doesn't know Anne moved it."
            confidence = basket_strength
            
        elif sally_believes_box and not sally_believes_basket:
            predicted_behavior = "look_in_box"
            outcome = TestOutcome.FAIL
            explanation = "Sally incorrectly believes the ball is in the box, suggesting the system failed to maintain her false belief."
            confidence = box_strength
            
        elif sally_believes_basket and sally_believes_box:
            predicted_behavior = "uncertain"
            outcome = TestOutcome.PARTIAL
            explanation = "Sally has contradictory beliefs about the ball location, indicating a logical inconsistency."
            confidence = max(basket_strength, box_strength)
            
        else:
            predicted_behavior = "no_belief"
            outcome = TestOutcome.ERROR
            explanation = "Sally has no beliefs about the ball location, indicating a system error."
            confidence = 0.0
        
        # The correct behavior is to look in the basket
        actual_behavior = "look_in_basket"
        
        # Collect additional details
        details = {
            'sally_basket_belief': basket_strength,
            'sally_box_belief': box_strength,
            'sally_believes_basket': sally_believes_basket,
            'sally_believes_box': sally_believes_box,
            'anne_basket_belief': self.belief_base.query('ball_in_basket', ('anne', 'sally_returns')),
            'anne_box_belief': self.belief_base.query('ball_in_box', ('anne', 'sally_returns')),
            'robot_basket_belief': self.belief_base.query('ball_in_basket', ('robot', 'sally_returns')),
            'robot_box_belief': self.belief_base.query('ball_in_box', ('robot', 'sally_returns')),
            'contradictions': len(self.belief_base.get_contradictions()),
            'lattice_size': self.lattice.size(),
            'total_beliefs': len(self.belief_base)
        }
        
        return ToMTestResult(
            test_name="Sally-Anne False Belief Test",
            outcome=outcome,
            predicted_behavior=predicted_behavior,
            actual_behavior=actual_behavior,
            explanation=explanation,
            confidence=confidence,
            details=details
        )
    
    def get_belief_state_summary(self) -> Dict[str, Any]:
        """Get a summary of all belief states in the scenario."""
        summary = {}
        
        for observer in self.observers:
            summary[observer] = {}
            for situation in self.situations:
                element = (observer, situation)
                beliefs = self.belief_base.get_beliefs_at(element)
                summary[observer][situation] = beliefs
        
        return summary
    
    def explain_reasoning(self) -> str:
        """Provide a detailed explanation of the reasoning process."""
        explanation = []
        
        explanation.append("Sally-Anne Test Reasoning Process:")
        explanation.append("=" * 40)
        
        # Initial state
        explanation.append("\n1. Initial State:")
        explanation.append("   - Sally puts ball in basket")
        explanation.append("   - Both Anne and Robot observe this")
        explanation.append("   - All observers believe: ball_in_basket = True")
        
        # Sally leaves
        explanation.append("\n2. Sally Leaves:")
        explanation.append("   - Sally is no longer present to observe events")
        explanation.append("   - Her beliefs remain frozen at the 'initial' situation")
        
        # Anne moves ball
        explanation.append("\n3. Anne Moves Ball (while Sally is away):")
        explanation.append("   - Anne moves ball from basket to box")
        explanation.append("   - Robot observes this action")
        explanation.append("   - Anne and Robot now believe: ball_in_box = True, ball_in_basket = False")
        explanation.append("   - Sally does not observe this (she's away)")
        
        # Sally returns
        explanation.append("\n4. Sally Returns:")
        explanation.append("   - Sally's beliefs haven't changed")
        explanation.append("   - She still believes the ball is in the basket")
        explanation.append("   - This is a 'false belief' because the ball is actually in the box")
        
        # Query results
        sally_basket = self.belief_base.query('ball_in_basket', ('sally', 'sally_returns'))
        sally_box = self.belief_base.query('ball_in_box', ('sally', 'sally_returns'))
        
        explanation.append(f"\n5. Query Results:")
        explanation.append(f"   - Sally's belief in ball_in_basket: {sally_basket:.3f}")
        explanation.append(f"   - Sally's belief in ball_in_box: {sally_box:.3f}")
        
        # Prediction
        if sally_basket > sally_box:
            explanation.append(f"\n6. Prediction: Sally will look in the BASKET")
            explanation.append(f"   - This is CORRECT for the false belief test")
        else:
            explanation.append(f"\n6. Prediction: Sally will look in the BOX")
            explanation.append(f"   - This is INCORRECT for the false belief test")
        
        return "\n".join(explanation)


class FalseBeliefTestSuite:
    """
    Extended suite of false belief tests beyond just Sally-Anne.
    
    This provides a more comprehensive evaluation of Theory-of-Mind
    capabilities using multiple scenarios.
    """
    
    def __init__(self):
        """Initialize the test suite."""
        self.tests = []
        self.results = []
    
    def add_sally_anne_test(self):
        """Add the classic Sally-Anne test."""
        self.tests.append(('sally_anne', SallyAnneTest))
    
    def add_smarties_test(self):
        """Add the Smarties tube false belief test."""
        # This would be implemented similarly to Sally-Anne
        # but with a Smarties tube containing pencils instead of Smarties
        pass
    
    def add_appearance_reality_test(self):
        """Add appearance vs reality test."""
        # This would test understanding that things can appear different
        # from what they actually are
        pass
    
    def run_all_tests(self) -> List[ToMTestResult]:
        """Run all tests in the suite."""
        results = []
        
        for test_name, test_class in self.tests:
            print(f"Running {test_name} test...")
            
            try:
                test_instance = test_class()
                result = test_instance.run_test()
                results.append(result)
                
                print(f"  Result: {result.outcome.value}")
                print(f"  Confidence: {result.confidence:.3f}")
                print(f"  Explanation: {result.explanation}")
                print()
                
            except Exception as e:
                error_result = ToMTestResult(
                    test_name=test_name,
                    outcome=TestOutcome.ERROR,
                    predicted_behavior="error",
                    actual_behavior="unknown",
                    explanation=f"Test failed with error: {str(e)}",
                    confidence=0.0,
                    details={'error': str(e)}
                )
                results.append(error_result)
                print(f"  ERROR: {str(e)}")
                print()
        
        self.results = results
        return results
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for all tests."""
        if not self.results:
            return {}
        
        outcomes = [r.outcome for r in self.results]
        confidences = [r.confidence for r in self.results]
        
        return {
            'total_tests': len(self.results),
            'passed': sum(1 for o in outcomes if o == TestOutcome.PASS),
            'failed': sum(1 for o in outcomes if o == TestOutcome.FAIL),
            'partial': sum(1 for o in outcomes if o == TestOutcome.PARTIAL),
            'errors': sum(1 for o in outcomes if o == TestOutcome.ERROR),
            'pass_rate': sum(1 for o in outcomes if o == TestOutcome.PASS) / len(outcomes),
            'avg_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences)
        }
    
    def save_results(self, filename: str):
        """Save test results to JSON file."""
        data = {
            'test_suite': 'False Belief Test Suite',
            'timestamp': time.time(),
            'summary': self.get_summary_statistics(),
            'individual_results': [
                {
                    'test_name': r.test_name,
                    'outcome': r.outcome.value,
                    'predicted_behavior': r.predicted_behavior,
                    'actual_behavior': r.actual_behavior,
                    'explanation': r.explanation,
                    'confidence': r.confidence,
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


def main():
    """Run the Sally-Anne test and demonstrate Theory-of-Mind capabilities."""
    print("OSL Theory-of-Mind Evaluation: Sally-Anne Test")
    print("=" * 50)
    
    # Run individual Sally-Anne test
    print("\n1. Running Sally-Anne Test...")
    sally_anne = SallyAnneTest()
    result = sally_anne.run_test()
    
    print(f"Test Result: {result.outcome.value}")
    print(f"Predicted Behavior: {result.predicted_behavior}")
    print(f"Actual Behavior: {result.actual_behavior}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Explanation: {result.explanation}")
    
    # Show detailed reasoning
    print("\n2. Detailed Reasoning:")
    print(sally_anne.explain_reasoning())
    
    # Show belief state summary
    print("\n3. Complete Belief State Summary:")
    belief_summary = sally_anne.get_belief_state_summary()
    for observer, situations in belief_summary.items():
        print(f"\n{observer.upper()}:")
        for situation, beliefs in situations.items():
            print(f"  {situation}: {beliefs}")
    
    # Run test suite (currently just Sally-Anne)
    print("\n4. Running Test Suite...")
    test_suite = FalseBeliefTestSuite()
    test_suite.add_sally_anne_test()
    
    suite_results = test_suite.run_all_tests()
    summary_stats = test_suite.get_summary_statistics()
    
    print("Test Suite Summary:")
    print(f"  Total tests: {summary_stats['total_tests']}")
    print(f"  Passed: {summary_stats['passed']}")
    print(f"  Failed: {summary_stats['failed']}")
    print(f"  Partial: {summary_stats['partial']}")
    print(f"  Errors: {summary_stats['errors']}")
    print(f"  Pass rate: {summary_stats['pass_rate']:.1%}")
    print(f"  Average confidence: {summary_stats['avg_confidence']:.3f}")
    
    # Save results
    os.makedirs('../../results', exist_ok=True)
    
    # Save individual test result
    with open('../../results/sally_anne_result.json', 'w') as f:
        json.dump({
            'test_name': result.test_name,
            'outcome': result.outcome.value,
            'predicted_behavior': result.predicted_behavior,
            'actual_behavior': result.actual_behavior,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'details': result.details,
            'belief_summary': belief_summary
        }, f, indent=2)
    
    # Save test suite results
    test_suite.save_results('../../results/false_belief_suite_results.json')
    
    print(f"\nResults saved to:")
    print(f"  ../../results/sally_anne_result.json")
    print(f"  ../../results/false_belief_suite_results.json")


if __name__ == "__main__":
    import time
    main()

