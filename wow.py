#!/usr/bin/env python3

import sys
import os

# --- Python Version Check (MUST BE FIRST) ---
if sys.version_info < (3, 7):
    print("="*80 + "\nFATAL ERROR: INCOMPATIBLE PYTHON VERSION\n" + "="*80)
    print(f"This script requires Python 3.7 or newer. You are using {sys.version.split()[0]}.")
    print("Please update your Python installation from https://www.python.org/downloads/")
    sys.exit(1)

import subprocess
import shutil
import platform
import datetime
import logging
import time
import json
import re
from typing import List, Dict, Any, Optional, Callable, Tuple

# --- Venv and Dependency Management ---
VENV_DIR = ".venv"
LOG_DIR = "logs"
BENCHMARK_DIR = "benchmark_results"
LOG_FILE = os.path.join(LOG_DIR, "wowfactor.log")
REQUIREMENTS_FILE = "requirements.txt"
REQUIRED_PACKAGES = ["colorama", "prettytable", "prompt_toolkit", "psutil", "py-cpuinfo"]

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    for handler in logging.root.handlers[:]: logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s", handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler(sys.stdout)])

def check_and_setup_venv():
    with open(REQUIREMENTS_FILE, 'w') as f:
        for pkg in REQUIRED_PACKAGES: f.write(f"{pkg}\n")

    if sys.prefix == sys.base_prefix:
        setup_logging()
        logging.info("Not running in a virtual environment. Starting setup...")
        venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), VENV_DIR)
        venv_python_executable = os.path.join(venv_path, "Scripts", "python.exe") if platform.system() == "Windows" else os.path.join(venv_path, "bin", "python")

        if not os.path.exists(venv_path):
            logging.info(f"Creating virtual environment at {venv_path}...")
            try:
                subprocess.check_call([sys.executable, "-m", "venv", venv_path])
                logging.info("Virtual environment created successfully.")
            except Exception as e:
                logging.error(f"Fatal: Error creating virtual environment: {e}"); sys.exit(1)
        else:
            logging.info(f"Virtual environment already exists at {venv_path}.")

        logging.info(f"Installing/Updating dependencies from {REQUIREMENTS_FILE}...")
        try:
            subprocess.check_call([venv_python_executable, "-m", "pip", "install", "--upgrade", "-r", REQUIREMENTS_FILE])
            logging.info("Dependencies installed successfully.")
        except Exception as e:
            logging.error(f"Fatal: An unexpected error occurred during dependency installation: {e}"); sys.exit(1)

        logging.info("Setup complete. Re-launching script inside the virtual environment...")
        print("\n" + "="*80 + "\nSETUP COMPLETE. LAUNCHING APPLICATION...\n" + "="*80)
        time.sleep(1)
        try:
            result = subprocess.run([venv_python_executable, os.path.abspath(__file__)] + sys.argv[1:])
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            logging.info("Launcher process interrupted by user. Exiting.")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Fatal: Error re-launching script: {e}"); sys.exit(1)

    PKG_TO_MODULE_MAP = {'py-cpuinfo': 'cpuinfo'}
    try:
        for pkg in REQUIRED_PACKAGES:
            base_pkg_name = pkg.split('==')[0]
            module_name = PKG_TO_MODULE_MAP.get(base_pkg_name, base_pkg_name.replace('-', '_'))
            __import__(module_name)
    except ImportError as e:
        setup_logging()
        logging.critical(f"FATAL: A required package is missing even after setup: {e}")
        logging.critical("Please try deleting the '.venv' directory and running the script again.")
        sys.exit(1)

# --- Initial Setup Call ---
check_and_setup_venv()

# --- Imports after venv check ---
from colorama import init, Fore, Style
from prettytable import PrettyTable
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style as PromptStyle
import psutil
import cpuinfo

init(autoreset=True)
CLI_STYLE = PromptStyle.from_dict({'prompt': 'ansicyan bold', 'completion-menu.completion': 'bg:#008888 #ffffff', 'completion-menu.completion.current': 'bg:#00aaaa #000000'})

# --- Utility Functions ---
CONSOLE_WIDTH = 80

def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
def print_separator(): print("-" * CONSOLE_WIDTH)

# --- NEW ASCII ART ---
WOW_FACTOR_ASCII_ART = r"""
 __      __               ___________              __
/  \    /  \______  _  __ \_   _____/____    _____/  |_  ___________
\   \/\/   /  _ \ \/ \/ /  |    __) \__  \ _/ ___\   __\/  _ \_  __ \
 \        (  <_> )     /   |     \   / __ \\  \___|  | (  <_> )  | \/
  \__/\  / \____/ \/\_/    \___  /  (____  /\___  >__|  \____/|__|
       \/                      \/        \/     \/
"""

# --- Gradient and Color Definitions ---
RETRO_MAGENTA = Fore.MAGENTA + Style.BRIGHT; RETRO_CYAN = Fore.CYAN + Style.BRIGHT; RETRO_YELLOW = Fore.YELLOW + Style.BRIGHT; RETRO_GREEN = Fore.GREEN + Style.BRIGHT
RETRO_GOLD = Fore.YELLOW + Style.BRIGHT
RETRO_SILVER = Fore.WHITE + Style.BRIGHT
RETRO_BRONZE = Fore.LIGHTBLUE_EX + Style.BRIGHT
RETRO_NEON_GREEN = Fore.LIGHTGREEN_EX + Style.BRIGHT
RETRO_PURPLE = Fore.MAGENTA + Style.BRIGHT
RETRO_DARK_BLUE = Fore.BLUE + Style.BRIGHT

RETRO_GRADIENT_COLORS = [
    Fore.MAGENTA + Style.BRIGHT, Fore.LIGHTMAGENTA_EX + Style.BRIGHT, Fore.CYAN + Style.BRIGHT,
    Fore.LIGHTCYAN_EX + Style.BRIGHT, Fore.GREEN + Style.BRIGHT, Fore.LIGHTGREEN_EX + Style.BRIGHT,
    Fore.YELLOW + Style.BRIGHT, Fore.LIGHTYELLOW_EX + Style.BRIGHT, Fore.RED + Style.BRIGHT,
    Fore.LIGHTRED_EX + Style.BRIGHT
]

def print_gradient_ascii_art(ascii_art_string: str):
    lines = ascii_art_string.strip('\n').split('\n')
    num_colors = len(RETRO_GRADIENT_COLORS)
    for line_idx, line in enumerate(lines):
        colored_line = []
        for char_idx, char in enumerate(line):
            if char.isspace(): colored_line.append(char)
            else:
                color = RETRO_GRADIENT_COLORS[(char_idx + line_idx) % num_colors]
                colored_line.append(color + char)
        sys.stdout.write("".join(colored_line) + Style.RESET_ALL + "\n")
    sys.stdout.flush()

def colorize_text_gradient(text: str, colors: List[str]) -> str:
    if not colors: return text
    num_colors = len(colors)
    return "".join(colors[i % num_colors] + char for i, char in enumerate(text))

def get_user_input(prompt_text: str, completer: Optional[WordCompleter] = None) -> str: return prompt(prompt_text, completer=completer, style=CLI_STYLE)
def get_user_choice_from_list(items: List[Any], item_name: str = "item") -> Optional[int]:
    if not items: print(Fore.YELLOW + f"No {item_name}s available." + Style.RESET_ALL); return None
    print_separator(); print(Fore.CYAN + f"Select a {item_name}:" + Style.RESET_ALL)
    for i, item in enumerate(items): print(f"  {i + 1}. {item}")
    while True:
        try:
            choice_str = get_user_input(Fore.CYAN + f"Enter choice (1-{len(items)}) or 'b' to go back: " + Style.RESET_ALL).strip().lower()
            if choice_str == 'b': return None
            choice_int = int(choice_str)
            if 1 <= choice_int <= len(items): return choice_int - 1
            else: print(Fore.RED + f"Please enter a number between 1 and {len(items)}." + Style.RESET_ALL)
        except ValueError: print(Fore.RED + "Invalid input. Please enter a number or 'b'." + Style.RESET_ALL)
def confirm_action(prompt_text: str) -> bool:
    while True:
        response = get_user_input(Fore.YELLOW + f"{prompt_text} (y/n): " + Style.RESET_ALL).strip().lower()
        if response == 'y': return True
        if response == 'n': return False
        print(Fore.RED + "Invalid input. Please enter 'y' or 'n'." + Style.RESET_ALL)

# --- System and Performance ---
def clean_cpu_model_name(model_name: str) -> str:
    model_name = re.sub(r'\s+\d+-Core Processor', '', model_name, flags=re.IGNORECASE)
    model_name = re.sub(r'\s+with Radeon Graphics', '', model_name, flags=re.IGNORECASE)
    model_name = re.sub(r'\s*\(R\)|\(TM\)|@.*', '', model_name)
    return model_name.strip()

def get_cpu_info() -> Tuple[str, str, str]:
    cpu_model, cpu_freq_str, platform_name = "N/A", "N/A", "N/A"
    try:
        info = cpuinfo.get_cpu_info()
        raw_model = info.get('brand_raw', platform.processor())
        cpu_model = clean_cpu_model_name(raw_model)
        
        current_freq = psutil.cpu_freq()
        if current_freq:
            cpu_freq_str = f"{current_freq.current / 1000:.2f}GHz"
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
        logging.warning(f"Could not get detailed CPU info: {e}"); cpu_model = platform.processor()
    return cpu_model, cpu_freq_str, platform_name

# --- BENCHMARK MODE ---
def print_retro_header(dynamic_text: str):
    clear_screen(); border_char = "═"
    print(RETRO_MAGENTA + "╔" + border_char * (CONSOLE_WIDTH - 2) + "╗")
    print(RETRO_MAGENTA + "║" + " " * (CONSOLE_WIDTH - 2) + "║")
    print_gradient_ascii_art(WOW_FACTOR_ASCII_ART)
    print(RETRO_MAGENTA + "║" + " " * (CONSOLE_WIDTH - 2) + "║")
    colored_dynamic_text = colorize_text_gradient(dynamic_text, RETRO_GRADIENT_COLORS)
    padding = (CONSOLE_WIDTH - 2 - len(dynamic_text)) // 2
    print(RETRO_MAGENTA + "║" + " " * padding + colored_dynamic_text + Style.RESET_ALL + " " * (CONSOLE_WIDTH - 2 - len(dynamic_text) - padding) + RETRO_MAGENTA + "║")
    print(RETRO_MAGENTA + "╚" + border_char * (CONSOLE_WIDTH - 2) + "╝" + Style.RESET_ALL)

def display_and_save_benchmark_results(stats: Dict, duration: float):
    os.makedirs(BENCHMARK_DIR, exist_ok=True); timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); json_filename = os.path.join(BENCHMARK_DIR, f"results_{filename_ts}.json")
    ops = stats.get('total_ops', 0); ops_per_sec = ops / duration if duration > 0 else 0
    cpu_model, cpu_freq, platform_name = get_cpu_info()
    result_data = {
        "timestamp": timestamp, "duration_seconds": round(duration, 4), "total_operations": ops,
        "ops_per_second": round(ops_per_sec, 2),
        "system": {"platform": platform_name, "processor_model": cpu_model, "processor_frequency": cpu_freq}
    }
    try:
        with open(json_filename, 'w') as f: json.dump(result_data, f, indent=4)
        logging.info(f"Benchmark JSON results saved to '{json_filename}'")
    except Exception as e: logging.error(f"Failed to save benchmark JSON results: {e}")
    clear_screen(); print_retro_header("BENCHMARK COMPLETE")
    print(f"\n{RETRO_CYAN}Run Timestamp: {RETRO_YELLOW}{timestamp}")
    print_separator(); print(f"{RETRO_CYAN}CPU: {RETRO_GREEN}{cpu_model}"); print(f"{RETRO_CYAN}Live Frequency: {RETRO_GREEN}{cpu_freq}")
    print_separator(); table = PrettyTable(); table.field_names = [f"{RETRO_CYAN}Metric", f"{RETRO_CYAN}Value"]; table.align = "l"
    table.add_row([f"{RETRO_YELLOW}Total Operations", f"{RETRO_GREEN}{ops:,.0f}"]); table.add_row([f"{RETRO_YELLOW}Test Duration", f"{RETRO_GREEN}{duration:.2f} s"])
    table.add_row([f"{RETRO_GOLD}Operations Per Second", f"{RETRO_GOLD}{ops_per_sec:,.2f}"]); print(table); print(f"\n{RETRO_GREEN}Results file saved: {json_filename}")

def format_large_number(num: float) -> str:
    if num >= 1_000_000: return f"{num / 1_000_000:.2f}M"
    if num >= 1_000: return f"{num / 1_000:.2f}K"
    return f"{num:,.2f}"

def _get_all_valid_scores() -> List[Dict]:
    if not os.path.exists(BENCHMARK_DIR): os.makedirs(BENCHMARK_DIR)
    scores = []
    for filename in [f for f in os.listdir(BENCHMARK_DIR) if f.endswith('.json')]:
        try:
            with open(os.path.join(BENCHMARK_DIR, filename), 'r') as f:
                data = json.load(f)
                if 'ops_per_second' in data and 'system' in data and 'processor_model' in data.get('system', {}):
                    scores.append(data)
        except (json.JSONDecodeError, KeyError) as e: logging.warning(f"Could not parse or validate benchmark file '{filename}': {e}")
    return scores

def _render_scores_table(scores: List[Dict], title: str):
    print_retro_header(title)
    if not scores:
        print(RETRO_YELLOW + "\nNo benchmark results found. Run a benchmark to create one!".center(CONSOLE_WIDTH)); print_separator(); return

    table = PrettyTable()
    table.field_names = [f"{RETRO_CYAN}#", f"{RETRO_CYAN}DATE", f"{RETRO_CYAN}OPS", f"{RETRO_CYAN}OS", f"{RETRO_CYAN}CPU", f"{RETRO_CYAN}FREQ", f"{RETRO_CYAN}TOTAL OPS", f"{RETRO_CYAN}TIME"]
    table.align = "r"; table.align[f"{RETRO_CYAN}DATE"] = "l"; table.align[f"{RETRO_CYAN}OS"] = "l"; table.align[f"{RETRO_CYAN}CPU"] = "l"; table.align[f"{RETRO_CYAN}FREQ"] = "l"
    table.horizontal_char = '─'; table.vertical_char = '│'; table.junction_char = '┼'

    for i, score in enumerate(scores):
        rank = i + 1
        row_color = RETRO_DARK_BLUE
        if rank == 1: rank_display, row_color = f"{RETRO_GOLD}★{rank}★", RETRO_GOLD
        elif rank == 2: rank_display, row_color = f"{RETRO_SILVER}#{rank}#", RETRO_SILVER
        elif rank == 3: rank_display, row_color = f"{RETRO_BRONZE}#{rank}#", RETRO_BRONZE
        elif rank <= 10: rank_display, row_color = f"{RETRO_NEON_GREEN}{rank}", RETRO_NEON_GREEN
        else: rank_display = f"{RETRO_DARK_BLUE}{rank}"
        
        try:
            dt_obj = datetime.datetime.strptime(score.get('timestamp', ''), "%Y-%m-%d %H:%M:%S")
            date_str = dt_obj.strftime("%y-%m-%d %H:%M")
        except ValueError: date_str = score.get('timestamp', 'N/A')[:16]

        ops_str = format_large_number(score.get('ops_per_second', 0))
        system_info = score.get('system', {})
        platform_name = system_info.get('platform', 'N/A')
        cpu_model = system_info.get('processor_model', 'N/A')
        cpu_freq = system_info.get('processor_frequency', 'N/A')

        table.add_row([
            rank_display, f"{row_color}{date_str}", f"{row_color}{ops_str}",
            f"{row_color}{platform_name[:16].strip()}", f"{row_color}{cpu_model[:24].strip()}",
            f"{row_color}{cpu_freq[:8].strip()}", f"{row_color}{score.get('total_operations', 0):,}",
            f"{row_color}{score.get('duration_seconds', 0):.2f}s"
        ])
    print(table); print_separator()

def view_all_scores():
    all_scores = _get_all_valid_scores()
    all_scores.sort(key=lambda x: x.get('ops_per_second', 0), reverse=True)
    _render_scores_table(all_scores, "ALL SCORES (FULL LIST)")

def view_best_score_per_machine():
    all_scores = _get_all_valid_scores()
    if not all_scores:
        _render_scores_table([], "BEST SCORE PER MACHINE"); return

    machine_scores = {}
    for score in all_scores:
        system_info = score.get('system', {})
        machine_id = (system_info.get('processor_model'), system_info.get('platform'))
        if machine_id not in machine_scores: machine_scores[machine_id] = []
        machine_scores[machine_id].append(score)

    top_scores = []
    for machine_id, scores_list in machine_scores.items():
        best_score = sorted(scores_list, key=lambda x: x.get('ops_per_second', 0), reverse=True)[0]
        top_scores.append(best_score)

    top_scores.sort(key=lambda x: x.get('ops_per_second', 0), reverse=True)
    _render_scores_table(top_scores, "BEST SCORE PER MACHINE")

def compare_specific_cpu():
    all_scores = _get_all_valid_scores()
    if not all_scores:
        print_retro_header("COMPARE CPUs")
        print(RETRO_YELLOW + "\nNo benchmark results found to compare.".center(CONSOLE_WIDTH)); print_separator(); return

    cpu_models = sorted(list(set(s['system']['processor_model'] for s in all_scores)))
    
    print_retro_header("COMPARE CPUs")
    chosen_index = get_user_choice_from_list(cpu_models, "CPU to compare")

    if chosen_index is not None:
        selected_cpu = cpu_models[chosen_index]
        filtered_scores = [s for s in all_scores if s['system']['processor_model'] == selected_cpu]
        filtered_scores.sort(key=lambda x: x.get('ops_per_second', 0), reverse=True)
        _render_scores_table(filtered_scores, f"COMPARISON: {selected_cpu}")

def clear_invalid_scores():
    print_retro_header("CLEAR INVALID SCORES")
    if not os.path.exists(BENCHMARK_DIR):
        print(RETRO_YELLOW + "Benchmark directory not found. Nothing to do."); return
    json_files = [f for f in os.listdir(BENCHMARK_DIR) if f.endswith('.json')]
    if not json_files:
        print(RETRO_YELLOW + "No benchmark files found. Nothing to do."); return
    invalid_files = []
    for filename in json_files:
        try:
            with open(os.path.join(BENCHMARK_DIR, filename), 'r') as f:
                data = json.load(f)
                if 'ops_per_second' not in data or 'system' not in data or 'processor_model' not in data.get('system', {}):
                    invalid_files.append(filename)
        except (json.JSONDecodeError, KeyError): invalid_files.append(filename)
    if not invalid_files:
        print(RETRO_GREEN + "No invalid or outdated score files found."); return
    print(RETRO_YELLOW + "The following invalid/outdated score files were found:")
    for f in invalid_files: print(f"  - {f}")
    if confirm_action("\nDo you want to delete these files?"):
        deleted_count = 0
        for filename in invalid_files:
            try:
                os.remove(os.path.join(BENCHMARK_DIR, filename)); print(f"{RETRO_GREEN}Deleted: {filename}"); deleted_count += 1
            except OSError as e: print(f"{Fore.RED}Error deleting {filename}: {e}")
        logging.info(f"User deleted {deleted_count} invalid score files.")
        print(f"\n{RETRO_GREEN}Cleanup complete. {deleted_count} files deleted.")
    else:
        logging.info("User cancelled invalid score cleanup."); print(RETRO_YELLOW + "Cleanup cancelled.")

def _execute_single_benchmark_run(duration: float = 15.0, is_infinite: bool = False):
    stats = {'total_ops': 0}
    run_mode_text = "INFINITE" if is_infinite else f"{duration} seconds"
    print(f"\n{RETRO_GREEN}Starting benchmark for {run_mode_text}... (Press Ctrl+C to stop early){Style.RESET_ALL}"); logging.info(f"Starting benchmark for {run_mode_text}.")
    start_time = time.time()
    try:
        while True:
            if not is_infinite and (time.time() - start_time >= duration): break
            stats['total_ops'] += 1
            if stats['total_ops'] % 1000000 == 0:
                _update_live_feed(stats['total_ops'], time.time(), start_time)
    except KeyboardInterrupt:
        print(RETRO_YELLOW + "\n\nBenchmark stopped by user." + Style.RESET_ALL); logging.warning("Benchmark stopped by user.")
    finally:
        sys.stdout.write("\n"); sys.stdout.flush()
    actual_duration = time.time() - start_time
    logging.info(f"Benchmark finished. Total operations: {stats['total_ops']} in {actual_duration:.2f}s.")
    display_and_save_benchmark_results(stats, actual_duration)

def _update_live_feed(op_count: int, current_time: float, start_time: float):
    elapsed = current_time - start_time; ops_per_sec = op_count / elapsed if elapsed > 0 else 0
    sys.stdout.write(f"\r{RETRO_CYAN}OP: {op_count:<12,} | OPS: {ops_per_sec:,.0f}{Style.RESET_ALL} "); sys.stdout.flush()

def run_single_benchmark():
    print_retro_header("RUN NEW BENCHMARK"); print(RETRO_CYAN + "This will run a high-speed, automated test of the app's core functions."); print_separator()
    duration_input = get_user_input(RETRO_YELLOW + "Enter test duration in seconds (e.g., 15, or 0/infinite for endless): " + Style.RESET_ALL).strip().lower()
    is_infinite, duration = False, 15.0
    if duration_input in ['infinite', '0']:
        is_infinite = True
        print_separator(); print(RETRO_YELLOW + "WARNING: Infinite mode will run until you manually stop it (Ctrl+C).".center(CONSOLE_WIDTH)); print_separator()
        if not confirm_action(RETRO_YELLOW + "Proceed with infinite benchmark?"):
            print(RETRO_YELLOW + "Infinite run cancelled." + Style.RESET_ALL); return
    else:
        try: duration = float(duration_input)
        except ValueError: print(Fore.RED + "Invalid input. Defaulting to 15 seconds." + Style.RESET_ALL); duration = 15.0
        if duration <= 0: print(Fore.RED + "Duration must be positive. Defaulting to 15 seconds." + Style.RESET_ALL); duration = 15.0
    _execute_single_benchmark_run(duration=duration, is_infinite=is_infinite)

def run_batch_benchmark():
    print_retro_header("RUN BATCH BENCHMARK"); print(RETRO_CYAN + "Run multiple, consecutive benchmark tests."); print_separator()
    num_runs_input = get_user_input("Enter number of batch runs (2-100): ").strip()
    num_runs = int(num_runs_input) if num_runs_input.isdigit() and 2 <= int(num_runs_input) <= 100 else None
    if num_runs is None: print(Fore.RED + "Invalid number of runs. Batch run cancelled." + Style.RESET_ALL); return
    
    duration_input = get_user_input("Enter duration in seconds for each run (default: 15): ").strip()
    duration_per_run = int(duration_input) if duration_input.isdigit() and int(duration_input) > 0 else 15

    for i in range(num_runs):
        print_retro_header(f"BATCH RUN {i+1} OF {num_runs}")
        _execute_single_benchmark_run(duration=duration_per_run)
        if i < num_runs - 1:
            print(RETRO_YELLOW + f"\nCooldown... Next run starts in 3 seconds.{Style.RESET_ALL}"); time.sleep(3)
    print_retro_header("BATCH COMPLETE"); print(RETRO_GREEN + f"\nAll {num_runs} benchmark runs have finished." + Style.RESET_ALL)

def benchmark_menu():
    options = {
        '1': ("Run New Benchmark", run_single_benchmark), '2': ("Run Batch Benchmark", run_batch_benchmark), 
        '3': ("View Best Score per Machine", view_best_score_per_machine),
        '4': ("Compare a Specific CPU", compare_specific_cpu),
        '5': ("View All Scores (Full List)", view_all_scores),
        '6': ("Clear Invalid Scores", clear_invalid_scores),
        'q': ("Quit", None)
    }
    completer = WordCompleter(list(options.keys()))
    while True:
        print_retro_header("BENCHMARK INTERFACE")
        for key, (description, _) in options.items(): print(f"  {RETRO_YELLOW}{key}.{Style.RESET_ALL} {RETRO_CYAN}{description}")
        print_separator()
        choice = get_user_input(RETRO_YELLOW + "Awaiting command> " + Style.RESET_ALL, completer).strip().lower()
        if choice in options:
            action_name, action_func = options[choice]
            logging.info(f"User chose '{action_name}' from 'Benchmark Interface' menu.")
            if action_func is None: break
            action_func()
            if choice != 'q':
                input(RETRO_YELLOW + "\nPress Enter to return to Benchmark Interface..." + Style.RESET_ALL)
        else: print(RETRO_YELLOW + "COMMAND NOT RECOGNIZED."); time.sleep(1)

if __name__ == "__main__":
    try:
        setup_logging()
        logging.info("="*20 + " Application Session Started " + "="*20)
        benchmark_menu()
        logging.info("="*20 + " Application Session Ended " + "="*22)
        print(Fore.GREEN + "\nExiting. Goodbye!" + Style.RESET_ALL)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nApplication terminated by user." + Style.RESET_ALL)
        logging.warning("Application terminated by user (Ctrl+C).")
    except Exception as e:
        setup_logging()
        logging.critical(f"An unhandled exception occurred: {e}", exc_info=True)
        print(Fore.RED + f"A critical error occurred. Check {LOG_FILE} for details.")
    sys.exit(0)

# --- END OF SCRIPT ---