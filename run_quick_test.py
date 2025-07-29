#!/usr/bin/env python3
"""
Quick test of OSL implementation with smaller parameters.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def run_quick_rbp_test():
    """Run a quick RBP test with small parameters."""
    print("Running Quick RBP Test...")
    
    from experiments.performance.rbp_scaling import RBPScalingExperiment
    import numpy as np
    import random
    
    # Set seeds
    random.seed(42)
    np.random.seed(42)
    
    # Create directories
    results_dir = project_root / 'results'
    figures_dir = project_root / 'figures'
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    
    # Run quick experiment (smaller parameters)
    experiment = RBPScalingExperiment(max_size=500, trials=10)
    results = experiment.run_experiment()
    
    # Analyze complexity
    analysis = experiment.analyze_complexity()
    experiment.complexity_analysis = analysis
    
    print("\n" + "=" * 50)
    print("QUICK RBP TEST RESULTS")
    print("=" * 50)
    print(f"Empirical time exponent: {analysis['empirical_time_exponent']:.3f}")
    print(f"Classification: {analysis['classification']}")
    print(f"Is sub-linear: {analysis['is_sublinear_time']}")
    print(f"Close to √n: {analysis['is_sqrt_n_time']}")
    print(f"Time fit R²: {analysis['time_fit_r2']:.3f}")
    
    # Save results
    results_file = results_dir / 'rbp_quick_test.json'
    figures_file = figures_dir / 'rbp_quick_test.pdf'
    
    experiment.save_results(str(results_file))
    experiment.plot_results(str(figures_file))
    
    print(f"\n✓ Results saved to: {results_file}")
    print(f"✓ Plots saved to: {figures_file}")
    
    return analysis

def run_quick_tom_test():
    """Run a quick Theory-of-Mind test."""
    print("\nRunning Quick Sally-Anne Test...")
    
    from experiments.theory_of_mind.sally_anne import SallyAnneTest
    import json
    
    # Create directories
    results_dir = project_root / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # Run test
    sally_anne = SallyAnneTest()
    result = sally_anne.run_test()
    
    print(f"Test Result: {result.outcome.value}")
    print(f"Predicted: {result.predicted_behavior}")
    print(f"Confidence: {result.confidence:.3f}")
    
    # Save result
    result_file = results_dir / 'sally_anne_quick_test.json'
    with open(result_file, 'w') as f:
        json.dump({
            'test_name': result.test_name,
            'outcome': result.outcome.value,
            'predicted_behavior': result.predicted_behavior,
            'confidence': result.confidence,
            'explanation': result.explanation
        }, f, indent=2)
    
    print(f"✓ Results saved to: {result_file}")
    
    return result

def main():
    """Run quick tests."""
    print("OSL Quick Test Suite")
    print("=" * 30)
    
    try:
        # Quick RBP test
        rbp_analysis = run_quick_rbp_test()
        
        # Quick ToM test
        tom_result = run_quick_tom_test()
        
        print("\n" + "=" * 30)
        print("✅ QUICK TESTS COMPLETED")
        print("=" * 30)
        print(f"RBP: {rbp_analysis['classification']}")
        print(f"Exponent: {rbp_analysis['empirical_time_exponent']:.3f}")
        print(f"ToM: {tom_result.outcome.value}")
        
        # Check if files were created
        results_dir = project_root / 'results'
        figures_dir = project_root / 'figures'
        
        print(f"\nFiles created:")
        for file_path in results_dir.glob('*'):
            print(f"  {file_path}")
        for file_path in figures_dir.glob('*'):
            print(f"  {file_path}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

