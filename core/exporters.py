# core/exporters.py
# Export formatters for benchmark data in various formats.

import csv
import json
from typing import List, Dict, Any, Tuple


class XmlExporter:
    """
    Exports benchmark scores as XML format.
    
    Example output:
    <benchmarks>
      <benchmark id="1">
        <cpu>Intel Core i9-12900K</cpu>
        <score>15432</score>
        <timestamp>2024-01-15T10:30:00</timestamp>
      </benchmark>
    </benchmarks>
    """
    
    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export scores as XML to the specified file path.
        
        Args:
            scores: List of benchmark score dictionaries.
            filepath: Path where the XML file will be written.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<benchmarks>\n')
            
            for idx, score in enumerate(scores, start=1):
                # Extract relevant fields - handle both flat and nested structures
                system = score.get('system', {})
                cpu = score.get('processor_model', system.get('processor_model', 'Unknown'))
                score_value = score.get('ops_per_second', 0)
                timestamp = score.get('timestamp', '')
                platform = score.get('platform', system.get('platform', 'Unknown'))
                frequency = score.get('processor_frequency', system.get('processor_frequency', 'Unknown'))
                threads = score.get('num_threads', 1)
                
                f.write(f'  <benchmark id="{idx}">\n')
                f.write(f'    <cpu>{XmlExporter._escape_xml(cpu)}</cpu>\n')
                f.write(f'    <score>{score_value}</score>\n')
                f.write(f'    <timestamp>{XmlExporter._escape_xml(timestamp)}</timestamp>\n')
                f.write(f'    <platform>{XmlExporter._escape_xml(platform)}</platform>\n')
                f.write(f'    <frequency>{XmlExporter._escape_xml(str(frequency))}</frequency>\n')
                f.write(f'    <threads>{threads}</threads>\n')
                f.write('  </benchmark>\n')
            
            f.write('</benchmarks>\n')
    
    @staticmethod
    def _escape_xml(text: str) -> str:
        """
        Escape special XML characters.
        
        Args:
            text: The text to escape.
            
        Returns:
            The escaped text with special characters replaced by entities.
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


class YamlExporter:
    """
    Exports benchmark scores as YAML format.
    
    Example output:
    benchmarks:
      - cpu: Intel Core i9-12900K
        score: 15432
        timestamp: "2024-01-15T10:30:00"
    """
    
    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export scores as YAML to the specified file path.
        
        Args:
            scores: List of benchmark score dictionaries.
            filepath: Path where the YAML file will be written.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('benchmarks:\n')
            
            for score in scores:
                # Extract relevant fields - handle both flat and nested structures
                system = score.get('system', {})
                cpu = score.get('processor_model', system.get('processor_model', 'Unknown'))
                score_value = score.get('ops_per_second', 0)
                timestamp = score.get('timestamp', '')
                platform = score.get('platform', system.get('platform', 'Unknown'))
                frequency = score.get('processor_frequency', system.get('processor_frequency', 'Unknown'))
                threads = score.get('num_threads', 1)
                
                f.write(f'  - cpu: "{cpu}"\n')
                f.write(f'    score: {score_value}\n')
                f.write(f'    timestamp: "{timestamp}"\n')
                f.write(f'    platform: "{platform}"\n')
                f.write(f'    frequency: "{frequency}"\n')
                f.write(f'    threads: {threads}\n')


class CsvExporter:
    """
    Exports benchmark scores as CSV format with comprehensive metadata.
    
    Example output:
    id,cpu,score,timestamp,platform,frequency,threads,duration_seconds,total_operations
    1,"Intel Core i9-12900K",15432,"2024-01-15T10:30:00","Windows",4.2,8,15.0,231480
    """
    
    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """
        Export scores as CSV to the specified file path.
        
        Args:
            scores: List of benchmark score dictionaries.
            filepath: Path where the CSV file will be written.
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            
            # Write header row
            writer.writerow([
                'id',
                'cpu',
                'score',
                'timestamp',
                'platform',
                'frequency',
                'threads',
                'duration_seconds',
                'total_operations'
            ])

            # Write data rows
            for idx, score in enumerate(scores, start=1):
                system = score.get('system', {})
                cpu = score.get('processor_model', system.get('processor_model', 'Unknown'))
                score_value = score.get('ops_per_second', 0)
                timestamp = score.get('timestamp', '')
                platform = score.get('platform', system.get('platform', 'Unknown'))
                frequency = score.get('processor_frequency', system.get('processor_frequency', 'Unknown'))
                threads = score.get('num_threads', 1)
                duration = score.get('duration_seconds', 0)
                total_ops = score.get('total_operations', 0)

                writer.writerow([
                    idx,
                    cpu,
                    score_value,
                    timestamp,
                    platform,
                    frequency,
                    threads,
                    duration,
                    total_ops
                ])


class AnalyticsExporter:
    """
    Exports analytics summary reports in JSON format.
    
    Provides comprehensive export of statistical analysis results,
    trend data, and comparative metrics from the AnalyticsEngine.
    """
    
    @staticmethod
    def export_analytics_report(analytics_data: Dict[str, Any], filepath: str) -> None:
        """
        Export analytics summary report to JSON file.
        
        Args:
            analytics_data: Dictionary containing analytics summary data
                           from AnalyticsEngine.generate_summary_report()
            filepath: Path where the JSON file will be written
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analytics_data, f, indent=2)
    
    @staticmethod
    def export_stats_per_cpu(stats_per_model: Dict[str, Dict[str, float]], filepath: str) -> None:
        """
        Export statistics per CPU model to CSV format.
        
        Args:
            stats_per_model: Dictionary mapping CPU models to their statistics
            filepath: Path where the CSV file will be written
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow([
                'CPU Model',
                'Sample Count',
                'Ops/Sec Mean',
                'Ops/Sec Median',
                'Ops/Sec Std Dev',
                'Ops/Sec Min',
                'Ops/Sec Max',
                'Duration Mean (s)',
                'Total Ops Mean'
            ])
            
            # Write data rows
            for cpu_model, stats in stats_per_model.items():
                ops_stats = stats.get('ops_per_second', {})
                duration_stats = stats.get('duration_seconds', {})
                total_ops_stats = stats.get('total_operations', {})
                
                writer.writerow([
                    cpu_model,
                    stats.get('sample_count', 0),
                    ops_stats.get('mean', 0),
                    ops_stats.get('median', 0),
                    ops_stats.get('std_dev', 0),
                    ops_stats.get('min', 0),
                    ops_stats.get('max', 0),
                    duration_stats.get('mean', 0),
                    total_ops_stats.get('mean', 0)
                ])
    
    @staticmethod
    def export_trend_data(trends: Dict[str, Dict[str, Any]], filepath: str) -> None:
        """
        Export trend analysis data to CSV format.
        
        Args:
            trends: Dictionary mapping entities (CPU models or platforms)
                    to their trend analysis results
            filepath: Path where the CSV file will be written
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow([
                'Entity',
                'Trend Direction',
                'Change Rate (%)',
                'Volatility (CV)',
                'R-Squared',
                'First Value',
                'Last Value'
            ])
            
            # Write data rows
            for entity, trend_data in trends.items():
                writer.writerow([
                    entity,
                    trend_data.get('trend', ''),
                    trend_data.get('change_rate', 0),
                    trend_data.get('volatility', 0),
                    trend_data.get('r_squared', 0),
                    trend_data.get('first_value', 0),
                    trend_data.get('last_value', 0)
                ])
    
    @staticmethod
    def export_comparison_report(comparison_data: Dict[str, Any], filepath: str) -> None:
        """
        Export pairwise comparison report to JSON format.
        
        Args:
            comparison_data: Dictionary containing pairwise comparison results
                           from AnalyticsEngine.generate_comparison_report()
            filepath: Path where the JSON file will be written
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2)
    
    @staticmethod
    def export_rankings(rankings: List[Tuple[str, Dict]], filepath: str) -> None:
        """
        Export CPU model rankings to CSV format.
        
        Args:
            rankings: List of tuples (model_name, statistics) sorted by performance
            filepath: Path where the CSV file will be written
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow([
                'Rank',
                'CPU Model',
                'Mean Ops/Sec',
                'Median Ops/Sec',
                'Std Dev',
                'Min Ops/Sec',
                'Max Ops/Sec',
                'Sample Count'
            ])
            
            # Write data rows
            for rank, (model_name, stats) in enumerate(rankings, start=1):
                writer.writerow([
                    rank,
                    model_name,
                    stats.get('mean', 0),
                    stats.get('median', 0),
                    stats.get('std_dev', 0),
                    stats.get('min', 0),
                    stats.get('max', 0),
                    stats.get('count', 0)
                ])
    
    @staticmethod
    def export_outliers(outliers: List[Dict], filepath: str) -> None:
        """
        Export detected outliers to CSV format.
        
        Args:
            outliers: List of outlier dictionaries with score and z-score info
            filepath: Path where the CSV file will be written
        """
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow([
                'Timestamp',
                'CPU Model',
                'Score (Ops/Sec)',
                'Z-Score',
                'Deviation (%)'
            ])
            
            # Write data rows
            for outlier in outliers:
                score_data = outlier.get('score', {})
                writer.writerow([
                    score_data.get('timestamp', ''),
                    score_data.get('system', {}).get('processor_model', 'Unknown'),
                    score_data.get('ops_per_second', 0),
                    outlier.get('z_score', 0),
                    outlier.get('deviation_percent', 0)
                ])
    
    @staticmethod
    def export_summary_text_report(analytics_data: Dict[str, Any], filepath: str) -> None:
        """
        Export a human-readable text summary report.
        
        Args:
            analytics_data: Dictionary containing analytics summary data
            filepath: Path where the text file will be written
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write('=' * 60 + '\n')
            f.write('WOWFACTOR BENCHMARK ANALYTICS SUMMARY REPORT\n')
            f.write('=' * 60 + '\n\n')
            
            # Generation timestamp
            generated_at = analytics_data.get('generated_at', 'Unknown')
            f.write(f'Generated: {generated_at}\n\n')
            
            # Overall statistics
            overall_stats = analytics_data.get('overall_statistics', {})
            if overall_stats:
                f.write('-' * 40 + '\n')
                f.write('OVERALL STATISTICS\n')
                f.write('-' * 40 + '\n')
                f.write(f'Total Samples: {overall_stats.get("count", 0)}\n')
                f.write(f'Mean Score: {overall_stats.get("mean", 0):,.1f} ops/sec\n')
                f.write(f'Median Score: {overall_stats.get("median", 0):,.1f} ops/sec\n')
                f.write(f'Standard Deviation: {overall_stats.get("std_dev", 0):,.1f}\n')
                f.write(f'Range: {overall_stats.get("min", 0):,.0f} - {overall_stats.get("max", 0):,.0f}\n\n')
            
            # CPU model statistics
            cpu_stats = analytics_data.get('cpu_model_statistics', {})
            if cpu_stats:
                f.write('-' * 40 + '\n')
                f.write('CPU MODEL STATISTICS\n')
                f.write('-' * 40 + '\n\n')
                
                for model, stats in cpu_stats.items():
                    f.write(f'{model}:\n')
                    f.write(f'  Samples: {stats.get("count", 0)}\n')
                    f.write(f'  Mean: {stats.get("mean", 0):,.1f} ops/sec\n')
                    f.write(f'  Median: {stats.get("median", 0):,.1f} ops/sec\n')
                    f.write(f'  Std Dev: {stats.get("std_dev", 0):,.1f}\n')
                    f.write(f'  Min/Max: {stats.get("min", 0):,.0f}/{stats.get("max", 0):,.0f} ops/sec\n\n')
            
            # Trend analysis
            trends = analytics_data.get('trend_analysis', {})
            if trends:
                f.write('-' * 40 + '\n')
                f.write('TREND ANALYSIS\n')
                f.write('-' * 40 + '\n\n')
                
                for model, trend_data in trends.items():
                    direction = trend_data.get('direction', 'N/A')
                    if direction:
                        f.write(f'{model}: {direction.upper()}\n')
            
            # Performance rankings
            rankings = analytics_data.get('performance_rankings', [])
            if rankings:
                f.write('\n' + '-' * 40 + '\n')
                f.write('PERFORMANCE RANKINGS\n')
                f.write('-' * 40 + '\n\n')
                
                for rank, (model_name, stats) in enumerate(rankings[:10], start=1):  # Top 10
                    f.write(f'{rank}. {model_name}: {stats.get("mean", 0):,.1f} ops/sec\n')
            
            # Outliers section
            outliers = analytics_data.get('outliers_detected', [])
            if outliers:
                f.write('\n' + '-' * 40 + '\n')
                f.write(f'OUTLIERS DETECTED: {len(outliers)}\n')
                f.write('-' * 40 + '\n\n')
                
                for outlier in outliers[:5]:  # Show first 5
                    score_data = outlier.get('score', {})
                    f.write(f"- {score_data.get('system', {}).get('processor_model', 'Unknown')} "
                           f"({outlier.get('z_score', 0):.2f} std devs)\n")
            
            # Footer
            f.write('\n' + '=' * 60 + '\n')
            f.write('END OF REPORT\n')
            f.write('=' * 60 + '\n')
