"""
RBP Scaling Performance Experiment

This experiment measures the actual performance characteristics of the
Relativized Belief Propagation algorithm across different lattice sizes
and structures, providing honest empirical validation of theoretical claims.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import time
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Any
import json
import random
from dataclasses import dataclass

from osl import OSLattice, BeliefBase, RBPAlgorithm


@dataclass
class PerformanceResult:
    """Results from a single performance test."""
    lattice_size: int
    avg_propagation_time: float
    std_propagation_time: float
    avg_affected_elements: int
    std_affected_elements: int
    max_affected_elements: int
    lattice_height: int
    lattice_balanced: bool
    complexity_estimate: str


class RBPScalingExperiment:
    """
    Experiment to measure RBP scaling performance.
    
    This experiment creates lattices of varying sizes and measures the
    actual performance of RBP propagation, comparing against theoretical
    complexity bounds.
    """
    
    def __init__(self, max_size: int = 1000, trials: int = 50):
        """
        Initialize the scaling experiment.
        
        Args:
            max_size: Maximum lattice size to test
            trials: Number of trials per lattice size
        """
        self.max_size = max_size
        self.trials = trials
        self.results: List[PerformanceResult] = []
        
        # Test sizes (logarithmic scale)
        self.test_sizes = [int(x) for x in np.logspace(1, np.log10(max_size), 10)]
        
    def create_test_lattice(self, size: int) -> Tuple[OSLattice, bool]:
        """
        Create a test lattice of approximately the given size.
        
        Args:
            size: Target lattice size
            
        Returns:
            Tuple of (lattice, is_balanced)
        """
        # Calculate observer and situation counts to get close to target size
        # Try to make it roughly square for balance
        sqrt_size = int(np.sqrt(size))
        
        # Create observers and situations
        observers = [f"obs_{i}" for i in range(sqrt_size)]
        situations = [f"sit_{i}" for i in range(max(1, size // sqrt_size))]
        
        # Create partial orders to make the lattice interesting
        observer_order = []
        situation_order = []
        
        # Create chain-like orders for predictable structure
        for i in range(len(observers) - 1):
            if random.random() < 0.7:  # 70% chance of ordering
                observer_order.append((observers[i], observers[i + 1]))
        
        for i in range(len(situations) - 1):
            if random.random() < 0.7:
                situation_order.append((situations[i], situations[i + 1]))
        
        lattice = OSLattice(observers, situations, observer_order, situation_order)
        is_balanced = lattice.is_balanced(kappa=2.0)
        
        return lattice, is_balanced
    
    def run_single_test(self, lattice: OSLattice) -> Dict[str, Any]:
        """
        Run a single RBP performance test on the given lattice.
        
        Args:
            lattice: The lattice to test
            
        Returns:
            Dictionary with performance metrics
        """
        belief_base = BeliefBase(lattice, credibility_threshold=0.5)
        rbp = RBPAlgorithm(belief_base)
        
        # Add some initial beliefs
        num_initial_beliefs = min(100, lattice.size() // 2)
        for i in range(num_initial_beliefs):
            element = random.choice(lattice.elements)
            prop = f"prop_{i % 20}"  # Reuse some propositions
            weight = random.uniform(0.6, 1.0)
            
            record = belief_base.add_belief(prop, element, weight)
        
        # Measure propagation performance
        propagation_times = []
        affected_elements_counts = []
        
        for trial in range(self.trials):
            # Create a new belief to propagate
            element = random.choice(lattice.elements)
            prop = f"test_prop_{trial}"
            weight = random.uniform(0.6, 1.0)
            
            record = belief_base.add_belief(prop, element, weight, source="test")
            
            # Measure propagation time
            start_time = time.perf_counter()
            result = rbp.propagate(record)
            end_time = time.perf_counter()
            
            propagation_times.append(end_time - start_time)
            affected_elements_counts.append(len(result.affected_elements))
        
        return {
            'propagation_times': propagation_times,
            'affected_elements': affected_elements_counts,
            'complexity_estimate': rbp.get_complexity_estimate(random.choice(lattice.elements))
        }
    
    def run_experiment(self) -> List[PerformanceResult]:
        """
        Run the complete scaling experiment.
        
        Returns:
            List of PerformanceResult objects
        """
        print("Running RBP Scaling Performance Experiment")
        print(f"Testing lattice sizes up to {self.max_size} with {self.trials} trials each")
        print("-" * 60)
        
        results = []
        
        for size in self.test_sizes:
            print(f"Testing lattice size ~{size}...")
            
            # Create test lattice
            lattice, is_balanced = self.create_test_lattice(size)
            actual_size = lattice.size()
            
            print(f"  Actual size: {actual_size}, Balanced: {is_balanced}")
            
            # Run performance test
            test_results = self.run_single_test(lattice)
            
            # Calculate statistics
            times = test_results['propagation_times']
            affected = test_results['affected_elements']
            
            result = PerformanceResult(
                lattice_size=actual_size,
                avg_propagation_time=np.mean(times),
                std_propagation_time=np.std(times),
                avg_affected_elements=np.mean(affected),
                std_affected_elements=np.std(affected),
                max_affected_elements=max(affected),
                lattice_height=lattice.height(),
                lattice_balanced=is_balanced,
                complexity_estimate=test_results['complexity_estimate']['theoretical_complexity']
            )
            
            results.append(result)
            
            print(f"  Avg time: {result.avg_propagation_time:.6f}s ± {result.std_propagation_time:.6f}s")
            print(f"  Avg affected: {result.avg_affected_elements:.1f} ± {result.std_affected_elements:.1f}")
            print(f"  Max affected: {result.max_affected_elements}")
            print()
        
        self.results = results
        return results
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze the empirical complexity of RBP.
        
        Returns:
            Dictionary with complexity analysis
        """
        if not self.results:
            raise ValueError("No results to analyze. Run experiment first.")
        
        sizes = [r.lattice_size for r in self.results]
        times = [r.avg_propagation_time for r in self.results]
        affected = [r.avg_affected_elements for r in self.results]
        
        # Fit power law: time = a * size^b
        log_sizes = np.log(sizes)
        log_times = np.log(times)
        
        # Linear regression in log space
        coeffs_time = np.polyfit(log_sizes, log_times, 1)
        time_exponent = coeffs_time[0]
        
        # Same for affected elements
        log_affected = np.log(affected)
        coeffs_affected = np.polyfit(log_sizes, log_affected, 1)
        affected_exponent = coeffs_affected[0]
        
        # R-squared values
        time_r2 = np.corrcoef(log_sizes, log_times)[0, 1] ** 2
        affected_r2 = np.corrcoef(log_sizes, log_affected)[0, 1] ** 2
        
        # Theoretical predictions
        sqrt_n_times = [np.sqrt(s) * times[0] / np.sqrt(sizes[0]) for s in sizes]
        linear_times = [s * times[0] / sizes[0] for s in sizes]
        
        return {
            'empirical_time_exponent': time_exponent,
            'empirical_affected_exponent': affected_exponent,
            'time_fit_r2': time_r2,
            'affected_fit_r2': affected_r2,
            'is_sublinear_time': time_exponent < 1.0,
            'is_sqrt_n_time': abs(time_exponent - 0.5) < 0.2,
            'theoretical_sqrt_n': sqrt_n_times,
            'theoretical_linear': linear_times,
            'classification': self._classify_complexity(time_exponent)
        }
    
    def _classify_complexity(self, exponent: float) -> str:
        """Classify the empirical complexity based on the exponent."""
        if exponent < 0.3:
            return "Constant or logarithmic"
        elif exponent < 0.7:
            return "Sub-linear (close to √n)"
        elif exponent < 1.2:
            return "Linear"
        elif exponent < 1.8:
            return "Super-linear (close to n^1.5)"
        else:
            return "Quadratic or worse"
    
    def save_results(self, filename: str):
        """Save results to JSON file."""
        def convert_for_json(obj):
            """Convert objects to JSON-serializable format."""
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_for_json(item) for item in obj]
            else:
                return obj
        
        data = {
            'experiment_config': {
                'max_size': self.max_size,
                'trials': self.trials,
                'test_sizes': self.test_sizes
            },
            'results': [
                {
                    'lattice_size': int(r.lattice_size),
                    'avg_propagation_time': float(r.avg_propagation_time),
                    'std_propagation_time': float(r.std_propagation_time),
                    'avg_affected_elements': float(r.avg_affected_elements),
                    'std_affected_elements': float(r.std_affected_elements),
                    'max_affected_elements': int(r.max_affected_elements),
                    'lattice_height': int(r.lattice_height),
                    'lattice_balanced': bool(r.lattice_balanced),
                    'complexity_estimate': str(r.complexity_estimate)
                }
                for r in self.results
            ]
        }
        
        if hasattr(self, 'complexity_analysis'):
            data['complexity_analysis'] = convert_for_json(self.complexity_analysis)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def plot_results(self, save_path: str = None):
        """Create plots of the experimental results."""
        if not self.results:
            raise ValueError("No results to plot. Run experiment first.")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        sizes = [r.lattice_size for r in self.results]
        times = [r.avg_propagation_time for r in self.results]
        time_stds = [r.std_propagation_time for r in self.results]
        affected = [r.avg_affected_elements for r in self.results]
        affected_stds = [r.std_affected_elements for r in self.results]
        
        # Plot 1: Propagation time vs lattice size
        ax1.errorbar(sizes, times, yerr=time_stds, marker='o', capsize=5, label='Measured')
        
        # Add theoretical curves if analysis is available
        if hasattr(self, 'complexity_analysis'):
            analysis = self.complexity_analysis
            ax1.plot(sizes, analysis['theoretical_sqrt_n'], '--', label='Theoretical O(√n)', alpha=0.7)
            ax1.plot(sizes, analysis['theoretical_linear'], ':', label='Theoretical O(n)', alpha=0.7)
        
        ax1.set_xlabel('Lattice Size')
        ax1.set_ylabel('Propagation Time (s)')
        ax1.set_title('RBP Propagation Time vs Lattice Size')
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Affected elements vs lattice size
        ax2.errorbar(sizes, affected, yerr=affected_stds, marker='s', capsize=5, color='orange')
        ax2.set_xlabel('Lattice Size')
        ax2.set_ylabel('Affected Elements')
        ax2.set_title('Elements Affected by RBP vs Lattice Size')
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Lattice balance analysis
        balanced = [r.lattice_balanced for r in self.results]
        heights = [r.lattice_height for r in self.results]
        
        colors = ['green' if b else 'red' for b in balanced]
        ax3.scatter(sizes, heights, c=colors, alpha=0.7)
        ax3.set_xlabel('Lattice Size')
        ax3.set_ylabel('Lattice Height')
        ax3.set_title('Lattice Structure Analysis')
        ax3.set_xscale('log')
        ax3.grid(True, alpha=0.3)
        
        # Add legend for colors
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='green', label='Balanced'),
                          Patch(facecolor='red', label='Unbalanced')]
        ax3.legend(handles=legend_elements)
        
        # Plot 4: Performance summary
        if hasattr(self, 'complexity_analysis'):
            analysis = self.complexity_analysis
            
            # Create text summary
            summary_text = f"""
Empirical Complexity Analysis:

Time Complexity:
• Measured exponent: {analysis['empirical_time_exponent']:.3f}
• Classification: {analysis['classification']}
• R² fit: {analysis['time_fit_r2']:.3f}
• Sub-linear: {analysis['is_sublinear_time']}
• Close to √n: {analysis['is_sqrt_n_time']}

Affected Elements:
• Measured exponent: {analysis['empirical_affected_exponent']:.3f}
• R² fit: {analysis['affected_fit_r2']:.3f}

Performance Summary:
• Min lattice size: {min(sizes)}
• Max lattice size: {max(sizes)}
• Min time: {min(times):.6f}s
• Max time: {max(times):.6f}s
• Balanced lattices: {sum(balanced)}/{len(balanced)}
            """
            
            ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
                    verticalalignment='top', fontfamily='monospace', fontsize=9)
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.set_title('Performance Summary')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        
        return fig


def main():
    """Run the RBP scaling experiment."""
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    
    # Get the script directory and project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..')
    results_dir = os.path.join(project_root, 'results')
    figures_dir = os.path.join(project_root, 'figures')
    
    # Create directories
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    
    # Create and run experiment
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
    
    # Save results with absolute paths
    results_file = os.path.join(results_dir, 'rbp_scaling_results.json')
    figures_file = os.path.join(figures_dir, 'rbp_scaling_performance.pdf')
    
    experiment.save_results(results_file)
    experiment.plot_results(figures_file)
    
    print(f"\nResults saved to: {results_file}")
    print(f"Plots saved to: {figures_file}")


if __name__ == "__main__":
    main()

