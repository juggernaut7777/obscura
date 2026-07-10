#!/usr/bin/env python3
"""Remove stale 'blocked' and 'self-improve' learnings from brain memory."""
import json

MEMORY_FILE = "/home/user/ai-ugc/brain_memory.json"

POISON_WORDS = [
    "blocked",
    "broken and block",
    "self-improvement",
    "self_improve",
    "could not fix",
    "discover_tools",
    "do not use generate_model",
    "cookies expired",
]

with open(MEMORY_FILE) as f:
    data = json.load(f)

original = len(data.get("learnings", []))
data["learnings"] = [
    l for l in data.get("learnings", [])
    if not any(word in l.get("text", "").lower() for word in POISON_WORDS)
]
remaining = len(data["learnings"])

with open(MEMORY_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Removed {original - remaining} stale learnings, {remaining} remaining")
