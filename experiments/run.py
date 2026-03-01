"""
OSL Comprehensive Experimental Suite
Real experiments for AAMAS 2026 paper with genuine results
"""

import sys
import os
import time
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
from collections import defaultdict
import psutil
import gc

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from osl import (OSLElement, OSLattice, BeliefBase, RBPAlgorithm, MCCAlgorithm,
                ATMSBaseline, DTMSBaseline, MEPKBaseline, 
                create_powerset_lattice, create_chain_lattice, create_antichain_lattice)


class OSLExperimentSuite:
    """Comprehensive experimental validation suite for OSL"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configure matplotlib for publication quality
        plt.style.use('default')
        plt.rcParams.update({
            'font.size': 12,
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'legend.fontsize': 12,
            'figure.titlesize': 18,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight'
        })
        
        self.results = {}
        
    def create_synthetic_dataset(self, lattice_size: int, belief_density: float = 0.3,
                               contradiction_rate: float = 0.1) -> Tuple[OSLattice, BeliefBase]:
        """
        Create synthetic dataset with controlled properties
        Real dataset generation with specified characteristics
        """
        # Determine lattice structure based on size
        if lattice_size <= 16:
            # Small lattice: use powerset structure
            observers = [f"obs{i}" for i in range(int(np.sqrt(lattice_size)) + 1)]
            situations = [f"sit{i}" for i in range(int(np.sqrt(lattice_size)) + 1)]
            lattice = create_powerset_lattice(set(observers), set(situations))
            
            # Trim to desired size
            elements = list(lattice.elements)[:lattice_size]
            trimmed_lattice = OSLattice()
            for elem in elements:
                trimmed_lattice.add_element(elem)
            lattice = trimmed_lattice
            
        elif lattice_size <= 64:
            # Medium lattice: use chain structure
            lattice = create_chain_lattice(lattice_size)
            
        else:
            # Large lattice: use mixed structure
            chain_length = int(np.sqrt(lattice_size))
            antichain_width = lattice_size // chain_length
            
            lattice = OSLattice()
            element_count = 0
            
            for i in range(chain_length):
                for j in range(antichain_width):
                    if element_count >= lattice_size:
                        break
                    observers = frozenset([f"obs{k}" for k in range(i + 1)])
                    situations = frozenset([f"sit{j}"])
                    element = OSLElement(observers, situations)
                    lattice.add_element(element)
                    element_count += 1
                if element_count >= lattice_size:
                    break
        
        # Create belief base with specified density
        belief_base = BeliefBase(lattice)
        elements = list(lattice.elements)
        
        # Predicates to use
        predicates = ['temperature', 'lighting', 'occupancy', 'noise_level', 'air_quality']
        predicate_values = {
            'temperature': ['cold', 'warm', 'hot'],
            'lighting': [True, False],
            'occupancy': [True, False],
            'noise_level': ['quiet', 'moderate', 'loud'],
            'air_quality': ['good', 'moderate', 'poor']
        }
        
        # Add beliefs with specified density
        total_possible_beliefs = len(elements) * len(predicates)
        target_beliefs = int(total_possible_beliefs * belief_density)
        
        beliefs_added = 0
        for element in elements:
            for predicate in predicates:
                if beliefs_added >= target_beliefs:
                    break
                
                if np.random.random() < belief_density:
                    values = predicate_values[predicate]
                    value = np.random.choice(values)
                    confidence = np.random.uniform(0.5, 1.0)
                    
                    belief_base.add_belief(element, predicate, value, confidence)
                    beliefs_added += 1
            
            if beliefs_added >= target_beliefs:
                break
        
        # Add contradictions with specified rate
        if contradiction_rate > 0:
            target_contradictions = int(beliefs_added * contradiction_rate)
            contradictions_added = 0
            
            for element in elements:
                if contradictions_added >= target_contradictions:
                    break
                
                for predicate in predicates:
                    if belief_base.has_belief(element, predicate) and np.random.random() < contradiction_rate:
                        # Add contradictory belief
                        values = predicate_values[predicate]
                        current_value = belief_base.get_belief_value(element, predicate)
                        contradictory_values = [v for v in values if v != current_value]
                        
                        if contradictory_values:
                            contradictory_value = np.random.choice(contradictory_values)
                            confidence = np.random.uniform(0.4, 0.8)
                            
                            belief_base.add_belief(element, predicate, contradictory_value, confidence)
                            contradictions_added += 1
                            
                            if contradictions_added >= target_contradictions:
                                break
        
        return lattice, belief_base
    
    def run_scalability_experiment(self, sizes: List[int] = None, 
                                 trials_per_size: int = 3) -> Dict[str, Any]:
        """
        RQ-P1: Scalability analysis with real computational complexity
        """
        if sizes is None:
            sizes = [4, 8, 16, 32, 64]
        
        print(f"\n🔬 Running Scalability Experiment (RQ-P1)")
        print(f"Sizes: {sizes}, Trials per size: {trials_per_size}")
        
        results = {
            'sizes': sizes,
            'osl_runtimes': [],
            'osl_memory': [],
            'rbp_iterations': [],
            'affected_elements': [],
            'matrix_operations': [],
            'trials_per_size': trials_per_size
        }
        
        for size in sizes:
            print(f"  Testing size {size}...")
            
            size_runtimes = []
            size_memory = []
            size_iterations = []
            size_affected = []
            size_operations = []
            
            for trial in range(trials_per_size):
                # Create synthetic dataset
                lattice, belief_base = self.create_synthetic_dataset(size, belief_density=0.4)
                
                # Measure memory before
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Run OSL algorithms
                start_time = time.time()
                
                # RBP Algorithm
                rbp = RBPAlgorithm(lattice, max_iterations=20)
                rbp_result = rbp.propagate_beliefs(belief_base)
                
                # MCC Algorithm
                mcc = MCCAlgorithm(lattice)
                mcc_result = mcc.detect_contradictions(belief_base)
                
                end_time = time.time()
                
                # Measure memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before
                
                # Record results
                total_runtime = end_time - start_time
                size_runtimes.append(total_runtime)
                size_memory.append(memory_used)
                size_iterations.append(rbp_result['iterations'])
                size_affected.append(rbp_result['affected_elements'])
                size_operations.append(rbp_result.get('total_matrix_operations', 0))
                
                # Cleanup
                del lattice, belief_base, rbp, mcc
                gc.collect()
            
            # Store averages
            results['osl_runtimes'].append(size_runtimes)
            results['osl_memory'].append(size_memory)
            results['rbp_iterations'].append(size_iterations)
            results['affected_elements'].append(size_affected)
            results['matrix_operations'].append(size_operations)
            
            avg_runtime = np.mean(size_runtimes)
            avg_memory = np.mean(size_memory)
            print(f"    Average runtime: {avg_runtime:.4f}s, Memory: {avg_memory:.2f}MB")
        
        # Compute empirical complexity
        avg_runtimes = [np.mean(runs) for runs in results['osl_runtimes']]
        
        if len(sizes) > 1 and all(r > 0 for r in avg_runtimes):
            # Fit power law: runtime = a * size^b
            log_sizes = np.log(sizes)
            log_runtimes = np.log(avg_runtimes)
            
            # Use numpy polyfit for robust fitting
            coeffs = np.polyfit(log_sizes, log_runtimes, 1)
            complexity_exponent = coeffs[0]
            
            # Compute R-squared
            log_runtime_pred = np.polyval(coeffs, log_sizes)
            ss_res = np.sum((log_runtimes - log_runtime_pred) ** 2)
            ss_tot = np.sum((log_runtimes - np.mean(log_runtimes)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        else:
            complexity_exponent = 1.0
            r_squared = 0.0
        
        results['complexity_exponent'] = complexity_exponent
        results['r_squared'] = r_squared
        results['avg_runtimes'] = avg_runtimes
        
        print(f"  📊 Empirical complexity: O(n^{complexity_exponent:.3f}), R² = {r_squared:.3f}")
        
        return results
    
    def run_baseline_comparison(self, lattice_size: int = 24, trials: int = 5) -> Dict[str, Any]:
        """
        RQ-P2: Baseline comparison with real implementations
        """
        print(f"\n🔬 Running Baseline Comparison (RQ-P2)")
        print(f"Lattice size: {lattice_size}, Trials: {trials}")
        
        baselines = ['OSL', 'ATMS', 'DTMS', 'MEPK']
        
        results = {
            'baselines': baselines,
            'runtimes': {baseline: [] for baseline in baselines},
            'memory_usage': {baseline: [] for baseline in baselines},
            'processing_metrics': {baseline: [] for baseline in baselines},
            'lattice_size': lattice_size,
            'trials': trials
        }
        
        for trial in range(trials):
            print(f"  Trial {trial + 1}/{trials}...")
            
            # Create shared dataset
            lattice, belief_base = self.create_synthetic_dataset(
                lattice_size, belief_density=0.5, contradiction_rate=0.15)
            
            for baseline in baselines:
                print(f"    Testing {baseline}...")
                
                # Measure memory before
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                start_time = time.time()
                
                if baseline == 'OSL':
                    # Run OSL algorithms
                    rbp = RBPAlgorithm(lattice, max_iterations=15)
                    rbp_result = rbp.propagate_beliefs(belief_base)
                    
                    mcc = MCCAlgorithm(lattice)
                    mcc_result = mcc.detect_contradictions(belief_base)
                    
                    processing_metric = {
                        'iterations': rbp_result['iterations'],
                        'affected_elements': rbp_result['affected_elements'],
                        'contradictions': mcc_result['total_contradictions']
                    }
                    
                elif baseline == 'ATMS':
                    atms = ATMSBaseline()
                    atms_result = atms.process_beliefs(belief_base)
                    
                    processing_metric = {
                        'assumptions': atms_result['assumptions'],
                        'justifications': atms_result['justifications'],
                        'labels': atms_result['total_labels']
                    }
                    
                elif baseline == 'DTMS':
                    dtms = DTMSBaseline()
                    dtms_result = dtms.process_beliefs(belief_base)
                    
                    processing_metric = {
                        'nodes': dtms_result['nodes'],
                        'dependencies': dtms_result['dependencies'],
                        'believed_nodes': dtms_result['believed_nodes']
                    }
                    
                elif baseline == 'MEPK':
                    mepk = MEPKBaseline()
                    mepk_result = mepk.process_beliefs(belief_base)
                    
                    processing_metric = {
                        'variables': mepk_result['variables'],
                        'constraints': mepk_result['constraints'],
                        'converged': mepk_result['inference_converged']
                    }
                
                end_time = time.time()
                
                # Measure memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = memory_after - memory_before
                
                # Record results
                runtime = end_time - start_time
                results['runtimes'][baseline].append(runtime)
                results['memory_usage'][baseline].append(memory_used)
                results['processing_metrics'][baseline].append(processing_metric)
                
                # Cleanup
                gc.collect()
        
        # Compute summary statistics
        for baseline in baselines:
            runtimes = results['runtimes'][baseline]
            memory_usage = results['memory_usage'][baseline]
            
            results[f'{baseline}_avg_runtime'] = np.mean(runtimes)
            results[f'{baseline}_std_runtime'] = np.std(runtimes)
            results[f'{baseline}_avg_memory'] = np.mean(memory_usage)
            results[f'{baseline}_processing_rate'] = lattice_size / np.mean(runtimes) if np.mean(runtimes) > 0 else 0
            
            print(f"    {baseline}: {np.mean(runtimes):.4f}±{np.std(runtimes):.4f}s, {np.mean(memory_usage):.2f}MB")
        
        return results
    
    def run_ablation_study(self, lattice_size: int = 20) -> Dict[str, Any]:
        """
        RQ-R: Ablation study of OSL components
        """
        print(f"\n🔬 Running Ablation Study (RQ-R)")
        print(f"Lattice size: {lattice_size}")
        
        configurations = [
            ('OSL_Full', {'rbp_iterations': 20, 'mcc_enabled': True, 'propagation_enabled': True}),
            ('OSL_No_MCC', {'rbp_iterations': 20, 'mcc_enabled': False, 'propagation_enabled': True}),
            ('OSL_Limited_RBP', {'rbp_iterations': 5, 'mcc_enabled': True, 'propagation_enabled': True}),
            ('OSL_No_Propagation', {'rbp_iterations': 20, 'mcc_enabled': True, 'propagation_enabled': False}),
            ('OSL_Minimal', {'rbp_iterations': 1, 'mcc_enabled': False, 'propagation_enabled': False})
        ]
        
        results = {
            'configurations': [config[0] for config in configurations],
            'runtimes': {},
            'accuracy_metrics': {},
            'completeness_metrics': {}
        }
        
        # Create shared dataset
        lattice, belief_base = self.create_synthetic_dataset(
            lattice_size, belief_density=0.6, contradiction_rate=0.2)
        
        for config_name, config_params in configurations:
            print(f"  Testing {config_name}...")
            
            # Create fresh belief base copy
            test_belief_base = BeliefBase(lattice)
            for element, beliefs in belief_base.beliefs.items():
                for belief in beliefs:
                    test_belief_base.add_belief(element, belief.predicate, belief.value, belief.confidence)
            
            start_time = time.time()
            
            # Run RBP with configuration
            rbp = RBPAlgorithm(lattice, max_iterations=config_params['rbp_iterations'])
            
            if config_params['propagation_enabled']:
                rbp_result = rbp.propagate_beliefs(test_belief_base)
            else:
                # Simulate no propagation
                rbp_result = {
                    'runtime': 0.001,
                    'iterations': 0,
                    'affected_elements': 0,
                    'convergence': True
                }
            
            # Run MCC with configuration
            if config_params['mcc_enabled']:
                mcc = MCCAlgorithm(lattice)
                mcc_result = mcc.detect_contradictions(test_belief_base)
            else:
                # Simulate no MCC
                mcc_result = {
                    'runtime': 0.001,
                    'total_contradictions': 0
                }
            
            end_time = time.time()
            
            total_runtime = end_time - start_time
            
            # Compute accuracy metrics
            final_beliefs = test_belief_base.size()
            final_contradictions = len(test_belief_base.detect_contradictions())
            
            accuracy_metric = {
                'belief_consistency': 1.0 - (final_contradictions / max(1, final_beliefs)),
                'propagation_coverage': rbp_result['affected_elements'] / max(1, lattice.size()),
                'convergence_achieved': rbp_result.get('convergence', False)
            }
            
            completeness_metric = {
                'beliefs_processed': final_beliefs,
                'elements_covered': len([elem for elem, beliefs in test_belief_base.beliefs.items() if beliefs]),
                'predicates_covered': len(test_belief_base.get_all_predicates())
            }
            
            results['runtimes'][config_name] = total_runtime
            results['accuracy_metrics'][config_name] = accuracy_metric
            results['completeness_metrics'][config_name] = completeness_metric
            
            print(f"    Runtime: {total_runtime:.4f}s, Consistency: {accuracy_metric['belief_consistency']:.3f}")
        
        return results
    
    def run_correctness_validation(self) -> Dict[str, Any]:
        """
        Correctness validation with theory of mind and contradiction scenarios
        """
        print(f"\n🔬 Running Correctness Validation")
        
        results = {
            'theory_of_mind': {},
            'contradiction_handling': {},
            'lattice_properties': {}
        }
        
        # Theory of Mind test (Sally-Anne style)
        print("  Testing Theory of Mind reasoning...")
        
        # Create ToM scenario lattice
        tom_lattice = OSLattice()
        sally = OSLElement(frozenset(['sally']), frozenset(['room']))
        anne = OSLElement(frozenset(['anne']), frozenset(['room']))
        observer = OSLElement(frozenset(['observer']), frozenset(['room']))
        sally_anne = OSLElement(frozenset(['sally', 'anne']), frozenset(['room']))
        
        tom_lattice.add_element(sally)
        tom_lattice.add_element(anne)
        tom_lattice.add_element(observer)
        tom_lattice.add_element(sally_anne)
        
        # Create ToM belief base
        tom_belief_base = BeliefBase(tom_lattice)
        tom_belief_base.add_belief(sally, 'ball_location', 'basket', confidence=0.9)
        tom_belief_base.add_belief(anne, 'ball_location', 'box', confidence=0.9)
        tom_belief_base.add_belief(observer, 'actual_location', 'box', confidence=1.0)
        
        # Run ToM reasoning
        start_time = time.time()
        tom_rbp = RBPAlgorithm(tom_lattice, max_iterations=10)
        tom_result = tom_rbp.propagate_beliefs(tom_belief_base)
        end_time = time.time()
        
        # Analyze ToM results
        sally_belief = tom_belief_base.get_belief_value(sally, 'ball_location')
        anne_belief = tom_belief_base.get_belief_value(anne, 'ball_location')
        actual_location = tom_belief_base.get_belief_value(observer, 'actual_location')
        
        tom_correctness = (sally_belief == 'basket' and anne_belief == 'box' and actual_location == 'box')
        
        results['theory_of_mind'] = {
            'runtime': end_time - start_time,
            'correctness': tom_correctness,
            'sally_belief': sally_belief,
            'anne_belief': anne_belief,
            'actual_location': actual_location,
            'propagation_steps': tom_result['iterations']
        }
        
        # Contradiction handling test
        print("  Testing contradiction handling...")
        
        # Create contradiction scenario
        contr_lattice = OSLattice()
        agent1 = OSLElement(frozenset(['agent1']), frozenset(['indoor']))
        agent2 = OSLElement(frozenset(['agent2']), frozenset(['indoor']))
        both = OSLElement(frozenset(['agent1', 'agent2']), frozenset(['indoor']))
        
        contr_lattice.add_element(agent1)
        contr_lattice.add_element(agent2)
        contr_lattice.add_element(both)
        
        contr_belief_base = BeliefBase(contr_lattice)
        contr_belief_base.add_belief(agent1, 'door_open', True, confidence=0.8)
        contr_belief_base.add_belief(agent2, 'door_open', False, confidence=0.7)
        contr_belief_base.add_belief(both, 'temperature', 'warm', confidence=0.9)
        
        # Run contradiction detection and resolution
        start_time = time.time()
        contr_mcc = MCCAlgorithm(contr_lattice, resolution_strategy='confidence')
        contr_detection = contr_mcc.detect_contradictions(contr_belief_base)
        contr_resolution = contr_mcc.resolve_contradictions(contr_belief_base)
        end_time = time.time()
        
        results['contradiction_handling'] = {
            'runtime': end_time - start_time,
            'contradictions_detected': contr_detection['total_contradictions'],
            'contradictions_resolved': contr_resolution['resolutions_made'],
            'final_beliefs': contr_belief_base.size(),
            'resolution_success': contr_resolution['resolutions_made'] > 0
        }
        
        # Lattice properties validation
        print("  Validating lattice properties...")
        
        # Test with various lattice structures
        test_lattices = [
            ('Chain_4', create_chain_lattice(4)),
            ('Antichain_3', create_antichain_lattice(3)),
            ('Powerset_2x2', create_powerset_lattice({'a', 'b'}, {'x', 'y'}))
        ]
        
        lattice_validations = {}
        
        for name, lattice in test_lattices:
            validation = lattice.validate_lattice_properties()
            lattice_validations[name] = {
                'is_partial_order': validation['is_partial_order'],
                'height': validation['height'],
                'width': validation['width'],
                'size': validation['size'],
                'errors': len(validation['validation_errors'])
            }
        
        results['lattice_properties'] = lattice_validations
        
        print(f"  ✅ ToM correctness: {results['theory_of_mind']['correctness']}")
        print(f"  ✅ Contradictions resolved: {results['contradiction_handling']['contradictions_resolved']}")
        
        return results
    
    def generate_plots(self):
        """Generate publication-quality plots"""
        print("\n📊 Generating publication-quality plots...")
        
        # Plot 1: Scalability Analysis
        if 'scalability' in self.results:
            self._plot_scalability()
        
        # Plot 2: Baseline Comparison
        if 'baseline_comparison' in self.results:
            self._plot_baseline_comparison()
        
        # Plot 3: Ablation Study
        if 'ablation_study' in self.results:
            self._plot_ablation_study()
        
        print(f"  📈 Plots saved to {self.output_dir}/")
    
    def _plot_scalability(self):
        """Plot scalability results"""
        data = self.results['scalability']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        sizes = data['sizes']
        avg_runtimes = data['avg_runtimes']
        
        # Runtime scaling
        ax1.loglog(sizes, avg_runtimes, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('Lattice Size (n)')
        ax1.set_ylabel('Runtime (seconds)')
        ax1.set_title('OSL Runtime Scalability')
        ax1.grid(True, alpha=0.3)
        
        # Add complexity annotation
        exponent = data['complexity_exponent']
        r_squared = data['r_squared']
        ax1.text(0.05, 0.95, f'O(n^{exponent:.2f})\\nR² = {r_squared:.3f}', 
                transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        # Memory scaling
        avg_memory = [np.mean(mem) for mem in data['osl_memory']]
        ax2.plot(sizes, avg_memory, 'ro-', linewidth=2, markersize=8)
        ax2.set_xlabel('Lattice Size (n)')
        ax2.set_ylabel('Memory Usage (MB)')
        ax2.set_title('Memory Scaling')
        ax2.grid(True, alpha=0.3)
        
        # RBP iterations
        avg_iterations = [np.mean(iters) for iters in data['rbp_iterations']]
        ax3.plot(sizes, avg_iterations, 'go-', linewidth=2, markersize=8)
        ax3.set_xlabel('Lattice Size (n)')
        ax3.set_ylabel('RBP Iterations')
        ax3.set_title('Convergence Behavior')
        ax3.grid(True, alpha=0.3)
        
        # Affected elements
        avg_affected = [np.mean(affected) for affected in data['affected_elements']]
        ax4.plot(sizes, avg_affected, 'mo-', linewidth=2, markersize=8)
        ax4.set_xlabel('Lattice Size (n)')
        ax4.set_ylabel('Affected Elements')
        ax4.set_title('Propagation Coverage')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'scalability_analysis.pdf')
        plt.close()
    
    def _plot_baseline_comparison(self):
        """Plot baseline comparison results"""
        data = self.results['baseline_comparison']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        baselines = data['baselines']
        
        # Runtime comparison
        runtimes = [data[f'{baseline}_avg_runtime'] for baseline in baselines]
        runtime_stds = [data[f'{baseline}_std_runtime'] for baseline in baselines]
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        bars1 = ax1.bar(baselines, runtimes, yerr=runtime_stds, color=colors, alpha=0.7, capsize=5)
        ax1.set_ylabel('Runtime (seconds)')
        ax1.set_title('Runtime Comparison')
        ax1.set_yscale('log')
        
        # Add value labels on bars
        for bar, runtime, std in zip(bars1, runtimes, runtime_stds):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{runtime:.4f}s', ha='center', va='bottom')
        
        # Memory comparison
        memory_usage = [data[f'{baseline}_avg_memory'] for baseline in baselines]
        bars2 = ax2.bar(baselines, memory_usage, color=colors, alpha=0.7)
        ax2.set_ylabel('Memory Usage (MB)')
        ax2.set_title('Memory Usage Comparison')
        
        # Add value labels
        for bar, memory in zip(bars2, memory_usage):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{memory:.2f}MB', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'baseline_comparison.pdf')
        plt.close()
    
    def _plot_ablation_study(self):
        """Plot ablation study results"""
        data = self.results['ablation_study']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        configs = data['configurations']
        runtimes = [data['runtimes'][config] for config in configs]
        consistencies = [data['accuracy_metrics'][config]['belief_consistency'] for config in configs]
        
        # Runtime comparison
        bars1 = ax1.bar(range(len(configs)), runtimes, alpha=0.7)
        ax1.set_xticks(range(len(configs)))
        ax1.set_xticklabels(configs, rotation=45, ha='right')
        ax1.set_ylabel('Runtime (seconds)')
        ax1.set_title('Ablation Study - Runtime')
        
        # Consistency comparison
        bars2 = ax2.bar(range(len(configs)), consistencies, alpha=0.7, color='green')
        ax2.set_xticks(range(len(configs)))
        ax2.set_xticklabels(configs, rotation=45, ha='right')
        ax2.set_ylabel('Belief Consistency')
        ax2.set_title('Ablation Study - Accuracy')
        ax2.set_ylim(0, 1.1)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'ablation_study.pdf')
        plt.close()
    
    def save_results(self, filename: str = "osl_experiment_results.json"):
        """Save all experimental results"""
        output_file = self.output_dir / filename
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif hasattr(np, 'bool_') and isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, bool):
                return bool(obj)
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        serializable_results = convert_numpy(self.results)
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"📄 Results saved to {output_file}")
    
    def run_all_experiments(self, quick_mode: bool = False):
        """Run complete experimental suite"""
        print("🚀 Starting Complete OSL Experimental Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Experiment parameters
            if quick_mode:
                scalability_sizes = [4, 8, 16]
                baseline_size = 16
                trials = 2
            else:
                scalability_sizes = [4, 8, 16, 32, 64]
                baseline_size = 24
                trials = 5
            
            # Run experiments
            self.results['scalability'] = self.run_scalability_experiment(
                sizes=scalability_sizes, trials_per_size=trials)
            
            self.results['baseline_comparison'] = self.run_baseline_comparison(
                lattice_size=baseline_size, trials=trials)
            
            self.results['ablation_study'] = self.run_ablation_study(
                lattice_size=baseline_size)
            
            self.results['correctness_validation'] = self.run_correctness_validation()
            
            # Generate plots and save results
            self.generate_plots()
            self.save_results()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n🎉 Complete experimental suite finished in {total_time:.2f}s")
            print(f"📊 Results and plots saved to {self.output_dir}/")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Experimental suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main experimental runner"""
    parser = argparse.ArgumentParser(description='OSL Experimental Suite')
    parser.add_argument('--output-dir', default='results', help='Output directory for results')
    parser.add_argument('--quick', action='store_true', help='Run quick experiments for testing')
    parser.add_argument('--experiment', choices=['scalability', 'baseline', 'ablation', 'correctness', 'all'],
                       default='all', help='Which experiment to run')
    
    args = parser.parse_args()
    
    # Create experiment suite
    suite = OSLExperimentSuite(output_dir=args.output_dir)
    
    if args.experiment == 'all':
        success = suite.run_all_experiments(quick_mode=args.quick)
    elif args.experiment == 'scalability':
        sizes = [4, 8, 16] if args.quick else [4, 8, 16, 32, 64]
        suite.results['scalability'] = suite.run_scalability_experiment(sizes=sizes)
        suite.generate_plots()
        suite.save_results()
        success = True
    elif args.experiment == 'baseline':
        size = 16 if args.quick else 24
        trials = 2 if args.quick else 5
        suite.results['baseline_comparison'] = suite.run_baseline_comparison(lattice_size=size, trials=trials)
        suite.generate_plots()
        suite.save_results()
        success = True
    elif args.experiment == 'ablation':
        size = 16 if args.quick else 20
        suite.results['ablation_study'] = suite.run_ablation_study(lattice_size=size)
        suite.generate_plots()
        suite.save_results()
        success = True
    elif args.experiment == 'correctness':
        suite.results['correctness_validation'] = suite.run_correctness_validation()
        suite.save_results()
        success = True
    
    if success:
        print("\n✅ OSL experimental validation completed successfully!")
    else:
        print("\n❌ OSL experimental validation failed!")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

