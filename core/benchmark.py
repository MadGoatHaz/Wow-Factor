# wow_core.py
# This module contains all data processing and benchmark functions from wow.py

import os
import datetime
import logging
import time
import json
import re
import platform
from typing import List, Dict, Any, Optional, Callable, Tuple
from collections import OrderedDict
import multiprocessing
import math
import threading
import queue
import warnings
from core.power import PowerPlanManager

# Module-level logger for structured logging
logger = logging.getLogger(__name__)

# Constants
LOG_DIR = "logs"
BENCHMARK_DIR = "benchmark_results"
LOG_FILE = os.path.join(LOG_DIR, "wowfactor.log")
WARMUP_DURATION = 5.0  # Seconds for warmup and frequency monitoring

# Cache implementation
_cache = OrderedDict()
_CACHE_TTL = 300  # 5 minutes TTL


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached item is still valid (not expired)"""
    if cache_key not in _cache:
        return False
    timestamp, _ = _cache[cache_key]
    return time.time() - timestamp < _CACHE_TTL


def _get_from_cache(cache_key: str) -> Any:
    """Get item from cache if valid"""
    if _is_cache_valid(cache_key):
        logger.debug("Cache hit: %s", cache_key)
        item = _cache.pop(cache_key)
        _cache[cache_key] = item
        return item[1]
    else:
        logger.debug("Cache miss: %s", cache_key)
        _cache.pop(cache_key, None)
        return None


def _set_in_cache(cache_key: str, value: Any) -> None:
    """Set item in cache"""
    _cache.pop(cache_key, None)
    _cache[cache_key] = (time.time(), value)
    if len(_cache) > 100:
        _cache.popitem(last=False)


def _invalidate_cache(cache_key: str) -> None:
    """Invalidate specific cache entry"""
    _cache.pop(cache_key, None)


def _invalidate_all_cache() -> None:
    """Invalidate all cache entries (deprecated — use _invalidate_for_cpu or _cleanup_expired_cache)."""
    warnings.warn(
        "_invalidate_all_cache is deprecated; use _invalidate_for_cpu(cpu) or _cleanup_expired_cache()",
        FutureWarning,
        stacklevel=2,
    )
    _cache.clear()


def _invalidate_for_cpu(cpu_model: str) -> None:
    """Invalidate all cache entries that contain the given CPU model string,
    plus the general aggregator caches that depend on all-score data."""
    keys_to_remove = []
    for k, (_ts, val) in _cache.items():
        val_str = str(val)
        if cpu_model in val_str:
            keys_to_remove.append(k)
    for k in keys_to_remove:
        _cache.pop(k, None)
    # Also clear aggregator caches that include results from all CPUs
    for key in ("_get_all_valid_scores", "get_best_score_per_machine",
                "get_unique_cpu_models"):
        _cache.pop(key, None)


def _cleanup_expired_cache() -> None:
    """Remove all cache entries whose TTL has expired."""
    now = time.time()
    expired_keys = [k for k, (ts, _v) in _cache.items()
                    if now - ts >= _CACHE_TTL]
    for k in expired_keys:
        _cache.pop(k, None)


def _monitor_cpu_freq(stop_event: threading.Event, freq_queue: queue.Queue) -> None:
    """
    Monitors CPU frequency in a separate thread.
    Puts the maximum seen frequency into the queue.
    """
    max_freq = 0.0
    import psutil

    while not stop_event.is_set():
        try:
            freqs = psutil.cpu_freq(percpu=True)
            if freqs:
                current_max = max(f.current for f in freqs)
                if current_max > max_freq:
                    max_freq = current_max
        except Exception:
            pass
        time.sleep(0.01)

    freq_queue.put(max_freq)


def clean_cpu_model_name(model_name: str) -> str:
    model_name = re.sub(r'\s+\d+-Core Processor', '', model_name, flags=re.IGNORECASE)
    model_name = re.sub(r'\s+with Radeon Graphics', '', model_name, flags=re.IGNORECASE)
    model_name = re.sub(r'\s*\(R\)|\(TM\)|@.*', '', model_name)
    return model_name.strip()


def get_cpu_info() -> Tuple[str, str, str]:
    cpu_model, cpu_freq_str, platform_name = "N/A", "N/A", "N/A"
    try:
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        raw_model = info.get('brand_raw', platform.processor())
        cpu_model = clean_cpu_model_name(raw_model)

        import psutil
        current_freqs = psutil.cpu_freq(percpu=True)
        if current_freqs:
            max_current = max(f.current for f in current_freqs)
            cpu_freq_str = f"{max_current / 1000:.2f}GHz"
        elif info.get('hz_advertised_friendly'):
            cpu_freq_str = info.get('hz_advertised_friendly')

        p_system = platform.system()
        if p_system == "Windows":
            build = platform.version().split('.')[-1]
            platform_name = f"Win {platform.release()} ({build})"
        elif p_system == "Linux":
            platform_name = f"Lin {platform.release().split('-')[0]}"
        elif p_system == "Darwin":
            platform_name = f"Mac {platform.release()}"
        else:
            platform_name = p_system

    except Exception as e:
        logger.warning("Could not get detailed CPU info: %s", e)
        cpu_model = platform.processor()
    return cpu_model, cpu_freq_str, platform_name


def format_large_number(num: float) -> str:
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if num >= 1_000:
        return f"{num / 1_000:.2f}K"
    return f"{num:,.2f}"


def _get_all_valid_scores() -> List[Dict]:
    cache_key = "_get_all_valid_scores"
    cached_result = _get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result

    if not os.path.exists(BENCHMARK_DIR):
        os.makedirs(BENCHMARK_DIR)
    scores = []
    for filename in [f for f in os.listdir(BENCHMARK_DIR) if f.endswith('.json')]:
        try:
            with open(os.path.join(BENCHMARK_DIR, filename), 'r') as f:
                data = json.load(f)
                if ('ops_per_second' in data and 'system' in data
                        and 'processor_model' in data.get('system', {})):
                    scores.append(data)
        except (json.JSONDecodeError, KeyError):
            pass
    _set_in_cache(cache_key, scores)
    return scores


def save_benchmark_results(stats: Dict, duration: float, num_threads: int = 1) -> Dict:
    logger.info("Saving benchmark results: %.2f ops/s, %.1f s, %d threads",
                stats.get('total_ops', 0) / duration if duration > 0 else 0,
                duration, num_threads)
    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = os.path.join(BENCHMARK_DIR, f"results_{filename_ts}.json")
    ops = stats.get('total_ops', 0)
    ops_per_sec = ops / duration if duration > 0 else 0
    cpu_model, cpu_freq, platform_name = get_cpu_info()

    if 'max_frequency' in stats:
        cpu_freq = stats['max_frequency']

    result_data = {
        "timestamp": timestamp,
        "duration_seconds": round(duration, 4),
        "total_operations": ops,
        "ops_per_second": round(ops_per_sec, 2),
        "num_threads": num_threads,
        "system": {
            "platform": platform_name,
            "processor_model": cpu_model,
            "processor_frequency": cpu_freq
        },
        "file_path": json_filename
    }
    try:
        with open(json_filename, 'w') as f:
            json.dump(result_data, f, indent=4)
        logger.info("Benchmark JSON results saved to '%s'", json_filename)
    except Exception as e:
        logger.error("Failed to save benchmark JSON results: %s", e)
    _invalidate_for_cpu(cpu_model)
    _cleanup_expired_cache()
    return result_data


def _cpu_workload(duration: float, warmup_time: float, queue: Any, is_infinite: bool = False) -> int:
    """
    CPU-intensive workload using heavy floating point math.
    Runs for a warmup period (results discarded) then for the specified duration.
    """
    warmup_end = time.time() + warmup_time
    while time.time() < warmup_end:
        for _ in range(100):
            _ = math.sin(123.456) * math.sqrt(789.012)

    start_time = time.time()
    local_ops = 0
    reported_ops = 0
    batch_size = 2000
    last_report_time = start_time

    try:
        while True:
            current_time = time.time()
            if not is_infinite and (current_time - start_time >= duration):
                break

            for i in range(batch_size):
                val = 1.000001 + (i % 100) * 0.001
                _ = (math.sin(val) * math.cos(val)
                     + math.sqrt(val)
                     + math.pow(val, 1.5)
                     + math.exp(val % 5)
                     + math.log(val + 10))

            local_ops += batch_size

            if current_time - last_report_time > 0.05:
                delta = local_ops - reported_ops
                if delta > 0:
                    try:
                        queue.put(delta)
                        reported_ops = local_ops
                        last_report_time = current_time
                    except Exception:
                        break

        delta = local_ops - reported_ops
        if delta > 0:
            try:
                queue.put(delta)
            except Exception:
                pass

    except KeyboardInterrupt:
        pass

    return local_ops


def execute_single_benchmark_run(
    duration: float = 15.0,
    is_infinite: bool = False,
    num_threads: int = 1,
    progress_callback: Optional[Callable[[int, float, float], None]] = None
) -> Dict:
    """
    Executes the benchmark using threads.
    Since _cpu_workload does pure C-math (math.sin, etc.) that releases the GIL,
    threads provide true parallelism on multi-core systems.
    """
    stats = {'total_ops': 0}
    benchmark_start = time.time()
    stop_monitoring = threading.Event()
    freq_queue = queue.Queue()

    logger.info("Starting benchmark: %ss (warmup %ss), %d threads, infinite=%s",
                duration, WARMUP_DURATION, num_threads, is_infinite)

    # CPU frequency monitoring thread
    monitor_thread = threading.Thread(
        target=_monitor_cpu_freq, args=(stop_monitoring, freq_queue))
    monitor_thread.daemon = True
    monitor_thread.start()

    work_queue = queue.Queue()

    # Start worker threads
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(
            target=_cpu_workload,
            args=(duration, WARMUP_DURATION, work_queue, is_infinite),
            daemon=True
        )
        threads.append(t)
        t.start()

    # Wait for warmup
    time.sleep(WARMUP_DURATION)

    stop_monitoring.set()
    monitor_thread.join()

    total_ops = 0

    while any(t.is_alive() for t in threads):
        while not work_queue.empty():
            try:
                total_ops += work_queue.get_nowait()
            except Exception:
                break

        current_time = time.time()
        if progress_callback and (current_time - benchmark_start > 0.1):
            if total_ops > 0:
                progress_callback(total_ops, current_time, benchmark_start)

        time.sleep(0.05)

    # Final drain
    while not work_queue.empty():
        try:
            total_ops += work_queue.get_nowait()
        except Exception:
            break

    # Join all threads
    for t in threads:
        t.join(timeout=30)

    stats['total_ops'] = total_ops

    actual_duration = time.time() - benchmark_start
    logger.info("Benchmark finished. Total operations: %d in %.2fs with %d threads.",
                stats['total_ops'], actual_duration, num_threads)
    return save_benchmark_results(stats, actual_duration, num_threads)


def get_best_score_per_machine() -> List[Dict]:
    cache_key = "get_best_score_per_machine"
    cached_result = _get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result

    all_scores = _get_all_valid_scores()
    if not all_scores:
        return []

    machine_scores = {}
    for score in all_scores:
        system_info = score.get('system', {})
        proc_model = str(system_info.get('processor_model', '')).strip()
        platform_name = str(system_info.get('platform', '')).strip()

        machine_id = (proc_model, platform_name)
        if machine_id not in machine_scores:
            machine_scores[machine_id] = []
        machine_scores[machine_id].append(score)

    top_scores = []
    for machine_id, scores_list in machine_scores.items():
        best_score = sorted(scores_list,
                            key=lambda x: x.get('ops_per_second', 0),
                            reverse=True)[0]
        top_scores.append(best_score)

    top_scores.sort(key=lambda x: x.get('ops_per_second', 0), reverse=True)
    _set_in_cache(cache_key, top_scores)
    return top_scores


def get_scores_for_cpu(cpu_model_name: str) -> List[Dict]:
    cache_key = f"get_scores_for_cpu_{cpu_model_name}"
    cached_result = _get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result

    all_scores = _get_all_valid_scores()
    filtered_scores = [s for s in all_scores
                       if s['system']['processor_model'] == cpu_model_name]
    _set_in_cache(cache_key, filtered_scores)
    return filtered_scores


def get_unique_cpu_models() -> List[str]:
    cache_key = "get_unique_cpu_models"
    cached_result = _get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result

    all_scores = _get_all_valid_scores()
    unique_models = sorted(list(set(
        s['system']['processor_model']
        for s in all_scores
        if 'system' in s and 'processor_model' in s['system']
    )))
    _set_in_cache(cache_key, unique_models)
    return unique_models


def cleanup_invalid_scores() -> List[str]:
    if not os.path.exists(BENCHMARK_DIR):
        return []
    json_files = [f for f in os.listdir(BENCHMARK_DIR) if f.endswith('.json')]
    if not json_files:
        return []

    invalid_files = []
    for filename in json_files:
        try:
            with open(os.path.join(BENCHMARK_DIR, filename), 'r') as f:
                data = json.load(f)
                if ('ops_per_second' not in data or 'system' not in data
                        or 'processor_model' not in data.get('system', {})):
                    invalid_files.append(filename)
        except (json.JSONDecodeError, KeyError):
            invalid_files.append(filename)

    deleted_files = []
    for filename in invalid_files:
        try:
            os.remove(os.path.join(BENCHMARK_DIR, filename))
            deleted_files.append(filename)
            logger.info("Deleted invalid score file: %s", filename)
        except OSError as e:
            logger.error("Error deleting %s: %s", filename, e)
    # Invalidate caches that depend on all-score data
    for key in ("_get_all_valid_scores", "get_best_score_per_machine",
                "get_unique_cpu_models"):
        _cache.pop(key, None)
    _cleanup_expired_cache()
    return deleted_files


def parse_date(date_str: str) -> Optional[datetime.datetime]:
    """Parse date string in various formats."""
    if not date_str:
        return None
    try:
        if ' ' in date_str:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        else:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.datetime.strptime(date_str, "%Y/%m/%d")
        except ValueError:
            return None


def is_date_in_range(
    date_val: datetime.datetime,
    start_date: Optional[datetime.datetime],
    end_date: Optional[datetime.datetime]
) -> bool:
    """Check if a date is within a range."""
    if not date_val:
        return False
    if start_date and date_val < start_date:
        return False
    if end_date and date_val > end_date:
        return False
    return True


def get_unique_platforms(scores: List[Dict]) -> List[str]:
    """Get list of unique platforms from scores."""
    return sorted(list(set(
        s.get('system', {}).get('platform', 'Unknown') for s in scores
    )))


def apply_all_filters(
    scores: List[Dict],
    search_term: str,
    start_date: Optional[datetime.datetime],
    end_date: Optional[datetime.datetime],
    platform_filter: str
) -> List[Dict]:
    """Apply all filters to the scores list."""
    filtered_scores = []
    search_lower = search_term.lower() if search_term else ""

    for score in scores:
        if (platform_filter
                and score.get('system', {}).get('platform') != platform_filter):
            continue

        if start_date or end_date:
            timestamp_str = score.get('timestamp')
            if timestamp_str:
                try:
                    score_date = datetime.datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if not is_date_in_range(score_date, start_date, end_date):
                        continue
                except ValueError:
                    pass
                if start_date or end_date:
                    pass

        if search_lower:
            cpu_model = score.get('system', {}).get('processor_model', '').lower()
            platform = score.get('system', {}).get('platform', '').lower()
            timestamp = score.get('timestamp', '').lower()
            ops_per_second = str(score.get('ops_per_second', '')).lower()

            if (search_lower not in cpu_model
                    and search_lower not in platform
                    and search_lower not in timestamp
                    and search_lower not in ops_per_second):
                continue

        filtered_scores.append(score)
    return filtered_scores


def aggregate_scores_by_cpu(
    data: List[Dict]
) -> Tuple[List[str], List[float]]:
    """
    Aggregates scores by CPU model, calculating the average score for each.
    """
    if not data:
        return [], []

    cpu_scores = {}
    for item in data:
        system_info = item.get('system', {})
        if not isinstance(system_info, dict):
            system_info = {}
        cpu = system_info.get('processor_model', 'Unknown')
        score = item.get('ops_per_second', 0)

        if cpu not in cpu_scores:
            cpu_scores[cpu] = []
        cpu_scores[cpu].append(score)

    sorted_cpus = sorted(cpu_scores.keys())
    averages = []
    for cpu in sorted_cpus:
        scores = cpu_scores[cpu]
        avg = sum(scores) / len(scores) if scores else 0
        averages.append(round(avg, 2))

    return sorted_cpus, averages


def get_score_distribution(
    data: List[Dict],
    bin_size: int = 500
) -> Tuple[List[str], List[int]]:
    """
    Calculates score distribution for histogram.
    """
    if not data:
        return [], []

    scores = []
    for d in data:
        val = d.get('ops_per_second', 0)
        if isinstance(val, (int, float)):
            scores.append(val)

    if not scores:
        return [], []

    min_score = min(scores)
    max_score = max(scores)

    start_bin = (int(min_score) // bin_size) * bin_size
    end_bin = (int(max_score) // bin_size) * bin_size + bin_size

    bins = OrderedDict()
    current = start_bin
    while current < end_bin:
        label = f"{current}-{current + bin_size}"
        bins[label] = 0
        current += bin_size

    for score in scores:
        bin_start = (int(score) // bin_size) * bin_size
        label = f"{bin_start}-{bin_start + bin_size}"
        if label in bins:
            bins[label] += 1

    return list(bins.keys()), list(bins.values())


def export_data_to_json(
    screen_instance: Any,
    screen_type: str,
    data: List[Dict]
) -> Dict:
    """Prepare data for JSON export with metadata."""
    return {
        "metadata": {
            "screen_type": screen_type,
            "export_format": "json",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "data": data if data is not None else []
    }


# setup_logging delegates to core.logging_config for centralized config
def setup_logging(
    level: Union[int, str] = "INFO",
    log_file: str = LOG_FILE
) -> None:
    """Initialize logging using the centralized logging_config module."""
    from core.logging_config import setup_logging as _setup_logging
    _setup_logging(level=level, log_file=log_file)