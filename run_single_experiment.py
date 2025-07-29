#!/usr/bin/env python3
"""
Run individual OSL experiments with proper path handling.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def run_rbp_experiment():
    """Run the RBP scaling experiment."""
    print("Running RBP Scaling Experiment...")
    
    # Import and run
    from experiments.performance.rbp_scaling import RBPScalingExperiment
    import numpy as np
    import random
    
    # Set seeds for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Create directories
    results_dir = project_root / 'results'
    figures_dir = project_root / 'figures'
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    
    # Run experiment
    experiment = RBPScalingExperiment(max_size=2000, trials=30)
    results = experiment.run_experiment()
    
    # Analyze complexity
    analysis = experiment.analyze_complexity()
    experiment.complexity_analysis = analysis
    
    print("\n" + "=" * 60)
    print("COMPLEXITY ANALYSIS RESULTS")
    print("=" * 60)
    print(f"Empirical time exponent: {analysis['empirical_time_exponent']:.3f}")
    print(f"Classification: {analysis['classification']}")
    print(f"Is sub-linear: {analysis['is_sublinear_time']}")
    print(f"Close to √n: {analysis['is_sqrt_n_time']}")
    print(f"Time fit R²: {analysis['time_fit_r2']:.3f}")
    print(f"Affected elements exponent: {analysis['empirical_affected_exponent']:.3f}")
    print(f"Affected fit R²: {analysis['affected_fit_r2']:.3f}")
    
    # Save results
    results_file = results_dir / 'rbp_scaling_results.json'
    figures_file = figures_dir / 'rbp_scaling_performance.pdf'
    
    experiment.save_results(str(results_file))
    experiment.plot_results(str(figures_file))
    
    print(f"\n✓ Results saved to: {results_file}")
    print(f"✓ Plots saved to: {figures_file}")
    
    return experiment, analysis

def run_sally_anne_test():
    """Run the Sally-Anne Theory-of-Mind test."""
    print("\nRunning Sally-Anne Theory-of-Mind Test...")
    
    from experiments.theory_of_mind.sally_anne import SallyAnneTest
    import json
    
    # Create directories
    results_dir = project_root / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # Run test
    sally_anne = SallyAnneTest()
    result = sally_anne.run_test()
    
    print(f"Test Result: {result.outcome.value}")
    print(f"Predicted Behavior: {result.predicted_behavior}")
    print(f"Actual Behavior: {result.actual_behavior}")
    print(f"Confidence: {result.confidence:.3f}")
    print(f"Explanation: {result.explanation}")
    
    # Save result
    result_file = results_dir / 'sally_anne_result.json'
    with open(result_file, 'w') as f:
        json.dump({
            'test_name': result.test_name,
            'outcome': result.outcome.value,
            'predicted_behavior': result.predicted_behavior,
            'actual_behavior': result.actual_behavior,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'details': result.details,
            'belief_summary': sally_anne.get_belief_state_summary()
        }, f, indent=2)
    
    print(f"✓ Results saved to: {result_file}")
    
    return result

def main():
    """Run all experiments."""
    print("OSL Honest Implementation - Individual Experiment Runner")
    print("=" * 60)
    
    try:
        # Run RBP experiment
        rbp_experiment, rbp_analysis = run_rbp_experiment()
        
        # Run Sally-Anne test
        tom_result = run_sally_anne_test()
        
        print("\n" + "=" * 60)
        print("✅ ALL EXPERIMENTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"RBP Complexity: {rbp_analysis['classification']}")
        print(f"RBP Exponent: {rbp_analysis['empirical_time_exponent']:.3f}")
        print(f"ToM Test: {tom_result.outcome.value}")
        print(f"ToM Confidence: {tom_result.confidence:.3f}")
        
        print(f"\nResults saved in: {project_root / 'results'}")
        print(f"Figures saved in: {project_root / 'figures'}")
        
    except Exception as e:
        print(f"\n❌ EXPERIMENT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

