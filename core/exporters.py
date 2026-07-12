# core/exporters.py
# Export formatters for benchmark data in various formats.

import csv
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def _sort_scores(scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort benchmark scores by ops_per_second descending."""
    return sorted(
        scores,
        key=lambda s: s.get('ops_per_second', 0),
        reverse=True
    )


def _build_metadata(source: str, record_count: int) -> Dict[str, Any]:
    """Build standard metadata for export."""
    return {
        'export_timestamp': datetime.now(timezone.utc).isoformat(),
        'source': source,
        'record_count': record_count
    }


class XmlExporter:
    """Exports benchmark scores as XML format."""

    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """Export scores as XML to the specified file path."""
        sorted_scores = _sort_scores(scores)
        metadata = _build_metadata('WowFactor Benchmark', len(sorted_scores))
        logger.info("Exporting %d scores to XML: %s", len(sorted_scores), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                ts = XmlExporter._escape_xml(metadata['export_timestamp'])
                src = XmlExporter._escape_xml(metadata['source'])
                cnt = metadata['record_count']
                f.write(
                    f'<benchmarks '
                    f'export_timestamp="{ts}" '
                    f'source="{src}" '
                    f'record_count="{cnt}">\n'
                )
                for idx, score in enumerate(sorted_scores, start=1):
                    system = score.get('system', {})
                    cpu = score.get(
                        'processor_model',
                        system.get('processor_model', 'Unknown'))
                    score_value = score.get('ops_per_second', 0)
                    timestamp = score.get('timestamp', '')
                    platform = score.get(
                        'platform',
                        system.get('platform', 'Unknown'))
                    frequency = score.get(
                        'processor_frequency',
                        system.get('processor_frequency', 'Unknown'))
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
        except IOError as e:
            logger.error("XML export failed for %s: %s", filepath, e)
            raise
        logger.info("XML export complete: %s", filepath)

    @staticmethod
    def _escape_xml(text: str) -> str:
        """Escape special XML characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


class YamlExporter:
    """Exports benchmark scores as YAML format."""

    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """Export scores as YAML to the specified file path."""
        sorted_scores = _sort_scores(scores)
        metadata = _build_metadata('WowFactor Benchmark', len(sorted_scores))
        logger.info("Exporting %d scores to YAML: %s", len(sorted_scores), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Metadata document
                f.write('# Benchmark Export Metadata\n')
                f.write(f'# export_timestamp: {metadata["export_timestamp"]}\n')
                f.write(f'# source: {metadata["source"]}\n')
                f.write(f'# record_count: {metadata["record_count"]}\n')
                f.write('---\n')
                f.write('benchmarks:\n')
                for score in sorted_scores:
                    system = score.get('system', {})
                    cpu = score.get(
                        'processor_model',
                        system.get('processor_model', 'Unknown'))
                    score_value = score.get('ops_per_second', 0)
                    timestamp = score.get('timestamp', '')
                    platform = score.get(
                        'platform',
                        system.get('platform', 'Unknown'))
                    frequency = score.get(
                        'processor_frequency',
                        system.get('processor_frequency', 'Unknown'))
                    threads = score.get('num_threads', 1)
                    f.write(f'  - cpu: "{cpu}"\n')
                    f.write(f'    score: {score_value}\n')
                    f.write(f'    timestamp: "{timestamp}"\n')
                    f.write(f'    platform: "{platform}"\n')
                    f.write(f'    frequency: "{frequency}"\n')
                    f.write(f'    threads: {threads}\n')
        except IOError as e:
            logger.error("YAML export failed for %s: %s", filepath, e)
            raise
        logger.info("YAML export complete: %s", filepath)


class CsvExporter:
    """Exports benchmark scores as CSV format with comprehensive metadata."""

    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """Export scores as CSV to the specified file path."""
        sorted_scores = _sort_scores(scores)
        metadata = _build_metadata('WowFactor Benchmark', len(sorted_scores))
        logger.info("Exporting %d scores to CSV: %s", len(sorted_scores), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                # Metadata comment row at top
                f.write(
                    f'# export_timestamp={metadata["export_timestamp"]}, '
                    f'source={metadata["source"]}, '
                    f'record_count={metadata["record_count"]}\n'
                )
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow([
                    'id', 'cpu', 'score', 'timestamp',
                    'platform', 'frequency', 'threads',
                    'duration_seconds', 'total_operations'
                ])
                for idx, score in enumerate(sorted_scores, start=1):
                    system = score.get('system', {})
                    cpu = score.get(
                        'processor_model',
                        system.get('processor_model', 'Unknown'))
                    score_value = score.get('ops_per_second', 0)
                    timestamp = score.get('timestamp', '')
                    platform = score.get(
                        'platform',
                        system.get('platform', 'Unknown'))
                    frequency = score.get(
                        'processor_frequency',
                        system.get('processor_frequency', 'Unknown'))
                    threads = score.get('num_threads', 1)
                    duration = score.get('duration_seconds', 0)
                    total_ops = score.get('total_operations', 0)
                    writer.writerow([
                        idx, cpu, score_value, timestamp,
                        platform, frequency, threads,
                        duration, total_ops
                    ])
        except IOError as e:
            logger.error("CSV export failed for %s: %s", filepath, e)
            raise
        logger.info("CSV export complete: %s", filepath)


class JsonExporter:
    """Exports benchmark scores as JSON format with metadata."""

    @staticmethod
    def export(scores: List[Dict[str, Any]], filepath: str) -> None:
        """Export scores as JSON to the specified file path."""
        sorted_scores = _sort_scores(scores)
        metadata = _build_metadata('WowFactor Benchmark', len(sorted_scores))
        logger.info("Exporting %d scores to JSON: %s", len(sorted_scores), filepath)
        try:
            output = {
                'metadata': metadata,
                'benchmarks': sorted_scores
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)
        except IOError as e:
            logger.error("JSON export failed for %s: %s", filepath, e)
            raise
        logger.info("JSON export complete: %s", filepath)


class AnalyticsExporter:
    """Exports analytics summary reports in JSON format."""

    @staticmethod
    def export_analytics_report(
        analytics_data: Dict[str, Any],
        filepath: str
    ) -> None:
        """Export analytics summary report to JSON file."""
        metadata = _build_metadata('WowFactor Analytics', 1)
        logger.info("Exporting analytics report to JSON: %s", filepath)
        try:
            output = {
                'metadata': metadata,
                **analytics_data
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)
            logger.info("Analytics JSON export complete: %s", filepath)
        except IOError as e:
            logger.error("Analytics JSON export failed for %s: %s",
                         filepath, e)
            raise

    @staticmethod
    def export_stats_per_cpu(
        stats_per_model: Dict[str, Dict[str, float]],
        filepath: str
    ) -> None:
        """Export statistics per CPU model to CSV format."""
        # Sort by mean ops_per_second descending
        sorted_models = sorted(
            stats_per_model.items(),
            key=lambda item: item[1].get('ops_per_second', {}).get('mean', 0),
            reverse=True
        )
        metadata = _build_metadata('WowFactor Stats', len(sorted_models))
        logger.info("Exporting stats for %d CPUs to CSV: %s",
                    len(sorted_models), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(
                    f'# export_timestamp={metadata["export_timestamp"]}, '
                    f'source={metadata["source"]}, '
                    f'record_count={metadata["record_count"]}\n'
                )
                writer = csv.writer(f)
                writer.writerow([
                    'CPU Model', 'Sample Count',
                    'Ops/Sec Mean', 'Ops/Sec Median',
                    'Ops/Sec Std Dev', 'Ops/Sec Min',
                    'Ops/Sec Max', 'Duration Mean (s)', 'Total Ops Mean'
                ])
                for cpu_model, stats in sorted_models:
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
        except IOError as e:
            logger.error("Stats CSV export failed for %s: %s",
                         filepath, e)
            raise
        logger.info("Stats CSV export complete: %s", filepath)

    @staticmethod
    def export_trend_data(
        trends: Dict[str, Dict[str, Any]],
        filepath: str
    ) -> None:
        """Export trend analysis data to CSV format."""
        metadata = _build_metadata('WowFactor Trends', len(trends))
        logger.info("Exporting trend data for %d entities to CSV: %s",
                    len(trends), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(
                    f'# export_timestamp={metadata["export_timestamp"]}, '
                    f'source={metadata["source"]}, '
                    f'record_count={metadata["record_count"]}\n'
                )
                writer = csv.writer(f)
                writer.writerow([
                    'Entity', 'Trend Direction', 'Change Rate (%)',
                    'Volatility (CV)', 'R-Squared',
                    'First Value', 'Last Value'
                ])
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
        except IOError as e:
            logger.error("Trend CSV export failed for %s: %s",
                         filepath, e)
            raise
        logger.info("Trend CSV export complete: %s", filepath)

    @staticmethod
    def export_comparison_report(
        comparison_data: Dict[str, Any],
        filepath: str
    ) -> None:
        """Export pairwise comparison report to JSON format."""
        metadata = _build_metadata('WowFactor Comparison', 1)
        logger.info("Exporting comparison report to JSON: %s", filepath)
        try:
            output = {
                'metadata': metadata,
                **comparison_data
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)
            logger.info("Comparison JSON export complete: %s", filepath)
        except IOError as e:
            logger.error("Comparison JSON export failed for %s: %s",
                         filepath, e)
            raise

    @staticmethod
    def export_rankings(
        rankings: List[Tuple[str, Dict]],
        filepath: str
    ) -> None:
        """Export CPU model rankings to CSV format."""
        # Sort by mean descending (rankings should be ordered by performance)
        sorted_rankings = sorted(
            rankings,
            key=lambda item: item[1].get('mean', 0),
            reverse=True
        )
        metadata = _build_metadata('WowFactor Rankings', len(sorted_rankings))
        logger.info("Exporting %d rankings to CSV: %s",
                    len(sorted_rankings), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(
                    f'# export_timestamp={metadata["export_timestamp"]}, '
                    f'source={metadata["source"]}, '
                    f'record_count={metadata["record_count"]}\n'
                )
                writer = csv.writer(f)
                writer.writerow([
                    'Rank', 'CPU Model', 'Mean Ops/Sec',
                    'Median Ops/Sec', 'Std Dev',
                    'Min Ops/Sec', 'Max Ops/Sec', 'Sample Count'
                ])
                for rank, (model_name, stats) in enumerate(sorted_rankings, start=1):
                    writer.writerow([
                        rank, model_name,
                        stats.get('mean', 0),
                        stats.get('median', 0),
                        stats.get('std_dev', 0),
                        stats.get('min', 0),
                        stats.get('max', 0),
                        stats.get('count', 0)
                    ])
        except IOError as e:
            logger.error("Rankings CSV export failed for %s: %s",
                         filepath, e)
            raise
        logger.info("Rankings CSV export complete: %s", filepath)

    @staticmethod
    def export_outliers(
        outliers: List[Dict],
        filepath: str
    ) -> None:
        """Export detected outliers to CSV format."""
        # Sort by ops_per_second descending
        sorted_outliers = sorted(
            outliers,
            key=lambda o: o.get('score', {}).get('ops_per_second', 0),
            reverse=True
        )
        metadata = _build_metadata('WowFactor Outliers', len(sorted_outliers))
        logger.info("Exporting %d outliers to CSV: %s",
                    len(sorted_outliers), filepath)
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(
                    f'# export_timestamp={metadata["export_timestamp"]}, '
                    f'source={metadata["source"]}, '
                    f'record_count={metadata["record_count"]}\n'
                )
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'CPU Model', 'Score (Ops/Sec)',
                    'Z-Score', 'Deviation (%)'
                ])
                for outlier in sorted_outliers:
                    score_data = outlier.get('score', {})
                    model = score_data.get('system', {}).get(
                        'processor_model', 'Unknown')
                    writer.writerow([
                        score_data.get('timestamp', ''),
                        model,
                        score_data.get('ops_per_second', 0),
                        outlier.get('z_score', 0),
                        outlier.get('deviation_percent', 0)
                    ])
        except IOError as e:
            logger.error("Outliers CSV export failed for %s: %s",
                         filepath, e)
            raise
        logger.info("Outliers CSV export complete: %s", filepath)

    @staticmethod
    def export_summary_text_report(
        analytics_data: Dict[str, Any],
        filepath: str
    ) -> None:
        """Export a human-readable text summary report."""
        export_timestamp = datetime.now(timezone.utc).isoformat()
        logger.info("Exporting summary text report: %s", filepath)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('=' * 60 + '\n')
                f.write('WOWFACTOR BENCHMARK ANALYTICS SUMMARY REPORT\n')
                f.write('=' * 60 + '\n\n')
                f.write(f'Generated: {export_timestamp}\n')
                f.write(f'Source: WowFactor Benchmark Suite\n')
                f.write(f'Format: Summary Text Report\n\n')

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

                trends = analytics_data.get('trend_analysis', {})
                if trends:
                    f.write('-' * 40 + '\n')
                    f.write('TREND ANALYSIS\n')
                    f.write('-' * 40 + '\n\n')
                    for model, trend_data in trends.items():
                        direction = trend_data.get('direction', 'N/A')
                        if direction:
                            f.write(f'{model}: {direction.upper()}\n')

                rankings = analytics_data.get('performance_rankings', [])
                if rankings:
                    f.write('\n' + '-' * 40 + '\n')
                    f.write('PERFORMANCE RANKINGS\n')
                    f.write('-' * 40 + '\n\n')
                    for rank, (model_name, stats) in enumerate(
                            rankings[:10], start=1):
                        f.write(f'{rank}. {model_name}: {stats.get("mean", 0):,.1f} ops/sec\n')

                outliers = analytics_data.get('outliers_detected', [])
                if outliers:
                    f.write('\n' + '-' * 40 + '\n')
                    f.write(f'OUTLIERS DETECTED: {len(outliers)}\n')
                    f.write('-' * 40 + '\n\n')
                    for outlier in outliers[:5]:
                        score_data = outlier.get('score', {})
                        model = score_data.get('system', {}).get(
                            'processor_model', 'Unknown')
                        z = outlier.get('z_score', 0)
                        f.write(f"- {model} ({z:.2f} std devs)\n")

                f.write('\n' + '=' * 60 + '\n')
                f.write('END OF REPORT\n')
                f.write('=' * 60 + '\n')
        except IOError as e:
            logger.error("Summary text export failed for %s: %s",
                         filepath, e)
            raise
        logger.info("Summary text report export complete: %s", filepath)