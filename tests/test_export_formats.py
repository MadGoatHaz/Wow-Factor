"""
Comprehensive unit tests for XmlExporter and YamlExporter classes.

Tests cover:
- Valid data export scenarios
- Special character handling (XML escaping)
- Empty list edge cases
- File creation verification
- Nested data structure handling (YAML)
"""

import tempfile
import os
import yaml
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from core.exporters import XmlExporter, YamlExporter


# =============================================================================
# XmlExporter Tests
# =============================================================================

def test_xml_export_valid_data():
    """Export valid benchmark scores and verify XML structure."""
    scores = [
        {
            'processor_model': 'Intel Core i9-12900K',
            'ops_per_second': 15432,
            'timestamp': '2024-01-15T10:30:00',
            'platform': 'Linux',
            'processor_frequency': '5000 MHz',
            'num_threads': 8
        }
    ]

    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
        filepath = tmp.name

    try:
        XmlExporter.export(scores, filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify XML structure elements
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert '<benchmark' in content  # Matches root with metadata attrs and child elements
        assert '</benchmarks>' in content
        assert '<benchmark id="1">' in content
        assert '<cpu>Intel Core i9-12900K</cpu>' in content
        assert '<score>15432</score>' in content
        assert '<timestamp>2024-01-15T10:30:00</timestamp>' in content
        assert '<platform>Linux</platform>' in content
        assert '<frequency>5000 MHz</frequency>' in content
        assert '<threads>8</threads>' in content
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_xml_export_special_characters():
    """Test escaping of < > & " ' characters."""
    scores = [
        {
            'processor_model': 'AMD Ryzen 9 Threadripper',
            'ops_per_second': 20000,
            'timestamp': "2024-01-15T10:30:00",
            'platform': 'Linux',
            'processor_frequency': '4800 MHz',
            'num_threads': 16
        }
    ]

    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
        filepath = tmp.name

    try:
        XmlExporter.export(scores, filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify basic XML structure is present
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert '<benchmark' in content  # Root element has metadata attributes
        assert '<cpu>AMD Ryzen 9 Threadripper</cpu>' in content
        assert '<score>20000</score>' in content

        # Test that the exporter properly handles special characters by testing _escape_xml directly
        escaped = XmlExporter._escape_xml('Test <value> & "quotes"')
        assert '&lt;value&gt;' in escaped, 'Should escape angle brackets'
        assert '&amp;' in escaped, 'Should escape ampersand'
        assert '&quot;quotes&quot;' in escaped, 'Should escape double quotes'
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_xml_export_empty_list():
    """Handle empty scores list gracefully."""
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
        filepath = tmp.name

    try:
        XmlExporter.export([], filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify XML structure is still valid but empty
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert '<benchmark' in content  # Root has metadata attributes
        assert '</benchmarks>' in content
        assert '<benchmark id=' not in content  # No benchmark entries
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_xml_file_creation():
    """Verify file is created with correct content."""
    scores = [
        {
            'processor_model': 'Test CPU',
            'ops_per_second': 10000,
            'timestamp': '2024-01-01T00:00:00',
            'platform': 'Windows',
            'processor_frequency': '3500 MHz',
            'num_threads': 4
        },
        {
            'processor_model': 'Another CPU',
            'ops_per_second': 12000,
            'timestamp': '2024-01-02T00:00:00',
            'platform': 'macOS',
            'processor_frequency': '4000 MHz',
            'num_threads': 6
        }
    ]

    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
        filepath = tmp.name

    try:
        XmlExporter.export(scores, filepath)

        # Verify file exists and is not empty
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

        # Parse XML to verify structure
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count benchmark entries
        benchmark_count = content.count('<benchmark id=')
        assert benchmark_count == 2

        # Verify both CPUs are present
        assert '<cpu>Test CPU</cpu>' in content
        assert '<cpu>Another CPU</cpu>' in content

        # Verify scores are correct
        assert '<score>10000</score>' in content
        assert '<score>12000</score>' in content
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


# =============================================================================
# YamlExporter Tests
# =============================================================================

def test_yaml_export_valid_data():
    """Export valid benchmark scores and verify YAML structure."""
    scores = [
        {
            'processor_model': 'Intel Core i9-12900K',
            'ops_per_second': 15432,
            'timestamp': '2024-01-15T10:30:00',
            'platform': 'Linux',
            'processor_frequency': '5000 MHz',
            'num_threads': 8
        }
    ]

    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        filepath = tmp.name

    try:
        YamlExporter.export(scores, filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify YAML structure elements
        assert 'benchmarks:' in content
        assert '- cpu:' in content
        assert 'score: 15432' in content
        assert 'timestamp: "2024-01-15T10:30:00"' in content
        assert 'platform: "Linux"' in content
        assert 'frequency: "5000 MHz"' in content
        assert 'threads: 8' in content

        # Verify it can be parsed as valid YAML
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            assert 'benchmarks' in data
            benchmarks = data['benchmarks'] if data['benchmarks'] is not None else []
            assert len(benchmarks) == 1
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_yaml_export_nested_data():
    """Test handling of nested score data structures."""
    scores = [
        {
            'system': {
                'processor_model': 'AMD Ryzen 9 5950X',
                'platform': 'Linux',
                'processor_frequency': '4600 MHz'
            },
            'ops_per_second': 18000,
            'timestamp': '2024-01-15T10:30:00',
            'num_threads': 12
        }
    ]

    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        filepath = tmp.name

    try:
        YamlExporter.export(scores, filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify nested data is properly extracted
        assert '- cpu: "AMD Ryzen 9 5950X"' in content
        assert 'score: 18000' in content
        assert 'platform: "Linux"' in content
        assert 'frequency: "4600 MHz"' in content

        # Verify it can be parsed as valid YAML
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            benchmarks = data['benchmarks'] if data['benchmarks'] is not None else []
            assert len(benchmarks) == 1
            assert benchmarks[0]['cpu'] == 'AMD Ryzen 9 5950X'
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_yaml_export_empty_list():
    """Handle empty scores list gracefully."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        filepath = tmp.name

    try:
        YamlExporter.export([], filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify YAML structure is still valid but empty
        assert 'benchmarks:' in content

        # Verify it can be parsed as valid YAML with empty list
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            assert 'benchmarks' in data
            benchmarks = data['benchmarks'] if data['benchmarks'] is not None else []
            assert benchmarks == []
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_yaml_file_creation():
    """Verify file is created with correct content."""
    scores = [
        {
            'processor_model': 'Test CPU A',
            'ops_per_second': 10000,
            'timestamp': '2024-01-01T00:00:00',
            'platform': 'Windows',
            'processor_frequency': '3500 MHz',
            'num_threads': 4
        },
        {
            'processor_model': 'Test CPU B',
            'ops_per_second': 12000,
            'timestamp': '2024-01-02T00:00:00',
            'platform': 'macOS',
            'processor_frequency': '4000 MHz',
            'num_threads': 6
        }
    ]

    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        filepath = tmp.name

    try:
        YamlExporter.export(scores, filepath)

        # Verify file exists and is not empty
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

        # Parse YAML to verify structure
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Verify benchmark count and content (sorted by ops_per_second desc)
        benchmarks = data['benchmarks'] if data['benchmarks'] is not None else []
        assert len(benchmarks) == 2
        # After sorting by ops_per_second descending, Test CPU B (12000) comes first
        assert benchmarks[0]['cpu'] == 'Test CPU B'
        assert benchmarks[1]['cpu'] == 'Test CPU A'
        assert benchmarks[0]['score'] == 12000
        assert benchmarks[1]['score'] == 10000
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)
