#!/usr/bin/env python3
"""Quick check of memory state size."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_memory import AgentMemory
m = AgentMemory()
s = m.get_state_summary()
print(f"STATE_SIZE: {len(s)} chars (~{len(s)//4} tokens)")
print(f"MODELS: {len(m.models)}")
print(f"PRODUCTS: {len(m.processed_products)}")
print(f"LEARNINGS: {len(m.learnings)}")
print(f"ACTION_LOG: {len(m.action_log)}")
# Print first 300 chars
print(f"PREVIEW: {s[:300]}")
