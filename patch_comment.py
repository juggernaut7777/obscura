import re

with open('goal2_sourcing_engine/all_in_one_bridge.py', 'r') as f:
    content = f.read()

# Add performance optimization comment as required by memory:
# "# ⚡ Performance optimization \n# Why: [reason] \n# What: [change]"
comment = """    # ⚡ Performance optimization
    # Why: time.sleep() blocks the entire process/thread. Using asyncio.sleep() allows non-blocking execution in potentially async web servers.
    # What: Replaced time.sleep with await asyncio.sleep in generate_image coroutine."""

content = content.replace("    if generate_image._consecutive_403s >= 3:", comment + "\n    if generate_image._consecutive_403s >= 3:")

with open('goal2_sourcing_engine/all_in_one_bridge.py', 'w') as f:
    f.write(content)
