import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import json
from datetime import datetime

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)
from algorithm_comparison import AdvancedSchedulingEngine, AlgorithmType, AlgorithmWeights
from models import db, User, Session, Assignment, Unavailability, UserRole, SkillLevel, FacilitatorSkill
import random
from dataclasses import asdict

class AlgorithmTester:
    """Comprehensive testing framework for scheduling algorithms"""
    
    def __init__(self):
        self.engine = AdvancedSchedulingEngine()
        self.test_results = []
        
    def run_single_test(self, algorithm: AlgorithmType, randomize: bool = False) -> Dict[str, Any]:
        """Run a single test with specified algorithm"""
        result = self.engine.generate_schedule(algorithm, randomize)
        result['timestamp'] = datetime.now().isoformat()
        return result
    
    def run_multiple_tests(self, algorithm: AlgorithmType, num_runs: int = 10) -> List[Dict[str, Any]]:
        """Run multiple tests with randomization to get statistical data"""
        results = []
        for i in range(num_runs):
            result = self.run_single_test(algorithm, randomize=True)
            result['run_number'] = i + 1
            results.append(result)
        return results
    
    def compare_all_algorithms(self, num_runs: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Test the threshold hybrid algorithm with multiple runs"""
        comparison_results = {}
        
        # Only test threshold hybrid algorithm
        algorithm = AlgorithmType.THRESHOLD_HYBRID
        print(f"Testing {algorithm.value}...")
        comparison_results[algorithm.value] = self.run_multiple_tests(algorithm, num_runs)
        
        return comparison_results
    
    def calculate_algorithm_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate statistical metrics for algorithm performance"""
        if not results or not any(r.get('success', False) for r in results):
            return {
                'avg_assignment_rate': 0.0,
                'std_assignment_rate': 0.0,
                'avg_score': 0.0,
                'std_score': 0.0,
                'success_rate': 0.0,
                'avg_conflicts': 0.0
            }
        
        successful_results = [r for r in results if r.get('success', False)]
        
        assignment_rates = [r.get('assignment_rate', 0) for r in successful_results]
        avg_scores = [r.get('avg_score', 0) for r in successful_results]
        conflicts = [len(r.get('conflicts', [])) for r in successful_results]
        
        return {
            'avg_assignment_rate': np.mean(assignment_rates),
            'std_assignment_rate': np.std(assignment_rates),
            'avg_score': np.mean(avg_scores),
            'std_score': np.std(avg_scores),
            'success_rate': len(successful_results) / len(results),
            'avg_conflicts': np.mean(conflicts),
            'min_score': np.min(avg_scores) if avg_scores else 0,
            'max_score': np.max(avg_scores) if avg_scores else 0
        }
    
    def generate_comparison_report(self, comparison_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate comprehensive comparison report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'algorithms': {},
            'summary': {},
            'recommendations': []
        }
        
        # Calculate statistics for each algorithm
        for algorithm_name, results in comparison_results.items():
            stats = self.calculate_algorithm_statistics(results)
            report['algorithms'][algorithm_name] = {
                'statistics': stats,
                'raw_results': results
            }
        
        # Generate summary and recommendations
        algorithm_stats = {name: data['statistics'] for name, data in report['algorithms'].items()}
        
        # Find best algorithm by different criteria
        best_assignment_rate = max(algorithm_stats.items(), key=lambda x: x[1]['avg_assignment_rate'])
        best_avg_score = max(algorithm_stats.items(), key=lambda x: x[1]['avg_score'])
        most_stable = min(algorithm_stats.items(), key=lambda x: x[1]['std_assignment_rate'])
        least_conflicts = min(algorithm_stats.items(), key=lambda x: x[1]['avg_conflicts'])
        
        report['summary'] = {
            'best_assignment_rate': {'algorithm': best_assignment_rate[0], 'value': best_assignment_rate[1]['avg_assignment_rate']},
            'best_avg_score': {'algorithm': best_avg_score[0], 'value': best_avg_score[1]['avg_score']},
            'most_stable': {'algorithm': most_stable[0], 'value': most_stable[1]['std_assignment_rate']},
            'least_conflicts': {'algorithm': least_conflicts[0], 'value': least_conflicts[1]['avg_conflicts']}
        }
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(algorithm_stats)
        
        return report
    
    def _generate_recommendations(self, algorithm_stats: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate algorithm recommendations based on statistics"""
        recommendations = []
        
        # Overall best performer
        overall_scores = {}
        max_score = max(s['avg_score'] for s in algorithm_stats.values())
        conflict_values = [s['avg_conflicts'] for s in algorithm_stats.values() if s['avg_conflicts'] > 0]
        max_conflicts = max(conflict_values) if conflict_values else 1.0
        
        for alg, stats in algorithm_stats.items():
            # Weighted score considering multiple factors
            score_factor = (stats['avg_score'] / max_score) * 0.3 if max_score > 0 else 0
            conflict_factor = (1 - stats['avg_conflicts'] / max_conflicts) * 0.1 if max_conflicts > 0 else 0.1
            
            overall_scores[alg] = (
                stats['avg_assignment_rate'] * 0.4 +
                score_factor +
                (1 - stats['std_assignment_rate']) * 0.2 +
                conflict_factor
            )
        
        best_overall = max(overall_scores.items(), key=lambda x: x[1])
        recommendations.append(f"Overall best algorithm: {best_overall[0]} (score: {best_overall[1]:.3f})")
        
        # Specific use case recommendations
        for alg, stats in algorithm_stats.items():
            if stats['avg_assignment_rate'] > 0.9:
                recommendations.append(f"{alg}: Excellent for high assignment coverage (>{stats['avg_assignment_rate']:.1%})")
            if stats['std_assignment_rate'] < 0.05:
                recommendations.append(f"{alg}: Very stable performance (std: {stats['std_assignment_rate']:.3f})")
            if stats['avg_conflicts'] < 2:
                recommendations.append(f"{alg}: Low conflict rate ({stats['avg_conflicts']:.1f} conflicts on average)")
        
        return recommendations
    
    def create_visualization_plots(self, comparison_results: Dict[str, List[Dict[str, Any]]], save_path: str = None):
        """Create comprehensive visualization plots for algorithm comparison"""
        # Set up the plotting style
        plt.style.use('default')
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Algorithm Performance Comparison Analysis', fontsize=18, fontweight='bold')
        
        # Prepare data for plotting
        plot_data = []
        for algorithm_name, results in comparison_results.items():
            for result in results:
                if result.get('success', False):
                    plot_data.append({
                        'Algorithm': algorithm_name.replace('_', ' ').title(),
                        'Assignment Rate': result.get('assignment_rate', 0) * 100,  # Convert to percentage
                        'Average Score': result.get('avg_score', 0),
                        'Conflicts': len(result.get('conflicts', [])),
                        'Score Std': result.get('score_std', 0),
                        'Min Score': result.get('min_score', 0),
                        'Max Score': result.get('max_score', 0)
                    })
        
        df = pd.DataFrame(plot_data)
        
        # Check if we have any data to plot
        if df.empty:
            print("Warning: No successful algorithm results to visualize")
            plt.close(fig)
            return None
        
        # Calculate means for bar charts
        algorithm_means = df.groupby('Algorithm').agg({
            'Assignment Rate': ['mean', 'std'],
            'Average Score': ['mean', 'std'],
            'Conflicts': ['mean', 'std'],
            'Score Std': 'mean'
        }).round(2)
        
        # Flatten column names
        algorithm_means.columns = ['_'.join(col).strip() for col in algorithm_means.columns]
        algorithm_means = algorithm_means.reset_index()
        
        # Plot 1: Assignment Rate Bar Chart with Error Bars
        x_pos = np.arange(len(algorithm_means))
        bars1 = axes[0, 0].bar(x_pos, algorithm_means['Assignment Rate_mean'], 
                              yerr=algorithm_means['Assignment Rate_std'],
                              capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        axes[0, 0].set_title('Assignment Success Rate Comparison (%)', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('Assignment Rate (%)', fontsize=12)
        axes[0, 0].set_xlabel('Algorithm Type', fontsize=12)
        axes[0, 0].set_xticks(x_pos)
        axes[0, 0].set_xticklabels(algorithm_means['Algorithm'], rotation=0, fontsize=10)
        axes[0, 0].grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
        
        # Plot 2: Average Score Bar Chart with Error Bars
        bars2 = axes[0, 1].bar(x_pos, algorithm_means['Average Score_mean'],
                              yerr=algorithm_means['Average Score_std'],
                              capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        axes[0, 1].set_title('Average Score Comparison', fontsize=14, fontweight='bold')
        axes[0, 1].set_ylabel('Average Score', fontsize=12)
        axes[0, 1].set_xlabel('Algorithm Type', fontsize=12)
        axes[0, 1].set_xticks(x_pos)
        axes[0, 1].set_xticklabels(algorithm_means['Algorithm'], rotation=0, fontsize=10)
        axes[0, 1].grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            axes[0, 1].text(bar.get_x() + bar.get_width()/2., height + 0.05,
                           f'{height:.2f}', ha='center', va='bottom', fontsize=10)
        
        # Plot 3: Conflicts Bar Chart
        bars3 = axes[0, 2].bar(x_pos, algorithm_means['Conflicts_mean'],
                              yerr=algorithm_means['Conflicts_std'],
                              capsize=5, alpha=0.8, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        axes[0, 2].set_title('Conflicts Comparison', fontsize=14, fontweight='bold')
        axes[0, 2].set_ylabel('Average Conflicts', fontsize=12)
        axes[0, 2].set_xlabel('Algorithm Type', fontsize=12)
        axes[0, 2].set_xticks(x_pos)
        axes[0, 2].set_xticklabels(algorithm_means['Algorithm'], rotation=0, fontsize=10)
        axes[0, 2].grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, bar in enumerate(bars3):
            height = bar.get_height()
            axes[0, 2].text(bar.get_x() + bar.get_width()/2., height + 0.2,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=10)
        
        # Plot 4: Line Chart - Performance Trends
        algorithms = algorithm_means['Algorithm'].tolist()
        assignment_rates = algorithm_means['Assignment Rate_mean'].tolist()
        avg_scores = [score * 20 for score in algorithm_means['Average Score_mean'].tolist()]  # Scale for visibility
        
        axes[1, 0].plot(algorithms, assignment_rates, marker='o', linewidth=2, markersize=8, label='Assignment Rate (%)')
        axes[1, 0].plot(algorithms, avg_scores, marker='s', linewidth=2, markersize=8, label='Average Score (×20)')
        axes[1, 0].set_title('Performance Trends Comparison', fontsize=14, fontweight='bold')
        axes[1, 0].set_ylabel('Value', fontsize=12)
        axes[1, 0].set_xlabel('Algorithm Type', fontsize=12)
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 5: Score Distribution Violin Plot
        sns.violinplot(data=df, x='Algorithm', y='Average Score', ax=axes[1, 1])
        axes[1, 1].set_title('Score Distribution Density', fontsize=14, fontweight='bold')
        axes[1, 1].set_ylabel('Average Score', fontsize=12)
        axes[1, 1].set_xlabel('Algorithm Type', fontsize=12)
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(axis='y', alpha=0.3)
        
        # Plot 6: Comprehensive Performance Radar-style Bar Chart
        # Normalize all metrics to 0-100 scale
        max_assignment = algorithm_means['Assignment Rate_mean'].max()
        max_score = algorithm_means['Average Score_mean'].max()
        max_conflicts = algorithm_means['Conflicts_mean'].max()
        
        normalized_data = {
            'Assignment Rate': (algorithm_means['Assignment Rate_mean'] / max_assignment * 100).tolist(),
            'Score Quality': (algorithm_means['Average Score_mean'] / max_score * 100).tolist(),
            'Low Conflicts': ((max_conflicts - algorithm_means['Conflicts_mean']) / max_conflicts * 100).tolist()
        }
        
        x = np.arange(len(algorithms))
        width = 0.25
        
        bars_ar = axes[1, 2].bar(x - width, normalized_data['Assignment Rate'], width, 
                                label='Assignment Rate', alpha=0.8, color='#1f77b4')
        bars_sq = axes[1, 2].bar(x, normalized_data['Score Quality'], width, 
                                label='Score Quality', alpha=0.8, color='#ff7f0e')
        bars_lc = axes[1, 2].bar(x + width, normalized_data['Low Conflicts'], width, 
                                label='Low Conflicts', alpha=0.8, color='#2ca02c')
        
        axes[1, 2].set_title('Comprehensive Performance Comparison (Normalized)', fontsize=14, fontweight='bold')
        axes[1, 2].set_ylabel('Normalized Score (0-100)', fontsize=12)
        axes[1, 2].set_xlabel('Algorithm Type', fontsize=12)
        axes[1, 2].set_xticks(x)
        axes[1, 2].set_xticklabels(algorithms, rotation=0, fontsize=10)
        axes[1, 2].legend()
        axes[1, 2].grid(axis='y', alpha=0.3)
        axes[1, 2].set_ylim(0, 110)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plots saved to {save_path}")
        
        plt.show()
        
        return fig
    
    def save_results_to_json(self, report: Dict[str, Any], filename: str = None):
        """Save comparison results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"algorithm_comparison_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
        
        print(f"Report saved to {filename}")
        return filename
    
    def run_comprehensive_test(self, num_runs: int = 10, save_plots: bool = True, save_report: bool = True):
        """Run comprehensive algorithm comparison test"""
        print("Starting comprehensive algorithm comparison...")
        print(f"Running {num_runs} tests per algorithm...")
        
        # Run comparison
        comparison_results = self.compare_all_algorithms(num_runs)
        
        # Generate report
        report = self.generate_comparison_report(comparison_results)
        
        # Create visualizations
        if save_plots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_filename = f"algorithm_comparison_plots_{timestamp}.png"
            self.create_visualization_plots(comparison_results, plot_filename)
        else:
            self.create_visualization_plots(comparison_results)
        
        # Save report
        if save_report:
            self.save_results_to_json(report)
        
        # Print summary
        print("\n" + "="*50)
        print("ALGORITHM COMPARISON SUMMARY")
        print("="*50)
        
        for algorithm_name, stats in report['algorithms'].items():
            print(f"\n{algorithm_name.upper()}:")
            print(f"  Assignment Rate: {stats['statistics']['avg_assignment_rate']:.2%} ± {stats['statistics']['std_assignment_rate']:.3f}")
            print(f"  Average Score: {stats['statistics']['avg_score']:.3f} ± {stats['statistics']['std_score']:.3f}")
            print(f"  Success Rate: {stats['statistics']['success_rate']:.2%}")
            print(f"  Average Conflicts: {stats['statistics']['avg_conflicts']:.1f}")
        
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\nBEST PERFORMERS:")
        print(f"  Best Assignment Rate: {report['summary']['best_assignment_rate']['algorithm']} ({report['summary']['best_assignment_rate']['value']:.2%})")
        print(f"  Best Average Score: {report['summary']['best_avg_score']['algorithm']} ({report['summary']['best_avg_score']['value']:.3f})")
        print(f"  Most Stable: {report['summary']['most_stable']['algorithm']} (std: {report['summary']['most_stable']['value']:.3f})")
        print(f"  Least Conflicts: {report['summary']['least_conflicts']['algorithm']} ({report['summary']['least_conflicts']['value']:.1f} conflicts)")
        
        return report

# Example usage and testing functions
def create_sample_data():
    """Create sample data for testing if database is empty"""
    # This function would create sample users, sessions, etc. for testing
    # Implementation depends on your specific database setup
    pass

if __name__ == "__main__":
    # Example usage
    tester = AlgorithmTester()
    
    # Run comprehensive test
    report = tester.run_comprehensive_test(num_runs=5)
    
    print("\nTest completed! Check the generated files for detailed results.")