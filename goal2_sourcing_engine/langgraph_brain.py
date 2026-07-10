"""
LangGraph Multi-Agent Orchestrator
==================================
Defines a stateful graph to coordinate the autonomous agent's tasks:
1. Scouting (Crawl4AI Scraping)
2. Designing (Image Vision QC & Ad Campaigns Generation)
3. Copywriting (Captions & Carousel Building)
4. Coordination (LiteLLM-based state routing)
"""
import asyncio
import sqlite3
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

# Define shared graph state
class AgentState(TypedDict):
    phase: str
    actions_today: int
    current_task: str
    next_step: str  # scout | designer | copywriter | wait | end
    error_list: List[str]
    recent_logs: List[str]
    context_data: Dict[str, Any]

# Try imports, fallback to mocks if packages aren't fully loaded yet
try:
    from langgraph.graph import StateGraph, END
    from litellm_router import shared_router
    from mem0_memory import Mem0Memory
    from crawl4ai_scraper import Crawl4AISourcingAgent
except ImportError:
    StateGraph = None
    END = "__end__"
    shared_router = None
    Mem0Memory = None
    Crawl4AISourcingAgent = None


# ─── AGENT NODES ───

async def coordinator_node(state: AgentState) -> AgentState:
    """Coordinator Node: Decisions made by LiteLLM router based on state."""
    print("\n[LANGGRAPH] Coordinator Node active. Inspecting system state...")
    
    # Init memory
    mem = Mem0Memory() if Mem0Memory else None
    state_summary = mem.get_state_summary() if mem else "Mock state summary."
    
    # Prompt for routing
    prompt = f"""You are the central Coordinator Agent for an autonomous fashion reselling assistant.
Your task is to analyze the current system state and route execution to the next specialized agent.

STATE SUMMARY:
{state_summary}

AVAILABLE AGENTS & RULES:
1. "scout": Trigger this if the product catalog contains less than 10 products ready to be processed, or if a supplier needs scanning.
2. "designer": Trigger this if there are scraped products ready in queue ('products_ready' is not empty). This agent creates high-quality ad campaigns.
3. "copywriter": Trigger this if there are completed ad campaigns that need captions and e-commerce carousel packaging.
4. "wait": Trigger this if the system is waiting for manual reviews on Discord or if there is no work to do.
5. "end": Trigger this if the session is complete.

Choose the single best next agent. Respond with JSON format only:
{{"next_agent": "scout"|"designer"|"copywriter"|"wait"|"end", "reason": "why you chose this"}}
"""
    
    next_agent = "wait"
    if shared_router:
        try:
            resp = await shared_router.get_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                primary_model="gemini-lite",
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content
            import json
            decision = json.loads(content)
            next_agent = decision.get("next_agent", "wait")
            print(f"[LANGGRAPH] Coordinator routed to: '{next_agent}' | Reason: {decision.get('reason')}")
        except Exception as e:
            print(f"[LANGGRAPH WARNING] Coordinator LLM call failed: {e}. Defaulting based on state...")
            
    # Relational state fallback if LLM is offline
    if next_agent == "wait" and mem:
        ready = mem.products_ready
        if len(ready) > 0:
            next_agent = "designer"
        else:
            next_agent = "scout"
            
    state["next_step"] = next_agent
    if mem:
        mem.log_action("Coordinator Decision", f"Routed to {next_agent}", True)
        
    return state


async def scout_node(state: AgentState) -> AgentState:
    """Scout Node: Crawls active suppliers (legit brands and blanks) and posts them to Discord."""
    print("\n[LANGGRAPH] Scout Node active. Crawling legit brands and basics...")
    mem = Mem0Memory() if Mem0Memory else None
    
    try:
        from auto_scout_v2 import run_scout
        # Run the scouter for legit brands and blanks (wrapped in asyncio.to_thread since it is synchronous)
        finds = await asyncio.to_thread(run_scout, "all", False, False, False)
        
        # Log findings into memory
        if finds and mem:
            for f in finds:
                mem.add_product({
                    "productName": f.get("name"),
                    "category": f.get("category", "top"),
                    "productUrl": f.get("url"),
                    "price": f.get("price", 0)
                })
            print(f"[LANGGRAPH SCOUT] Scouting complete. Found {len(finds)} new items.")
    except Exception as e:
        print(f"[LANGGRAPH ERROR] Scout node failed: {e}")
        state["error_list"].append(str(e))
    return state



async def designer_node(state: AgentState) -> AgentState:
    """Designer Node: Takes pending scraped product, runs VLM and starts generator."""
    print("\n[LANGGRAPH] Designer Node active. Processing ad graphics...")
    mem = Mem0Memory() if Mem0Memory else None
    
    if mem:
        ready_products = mem.products_ready
        if ready_products:
            prod = ready_products[0]
            print(f"[LANGGRAPH DESIGNER] Generating ad campaign for product: {prod.get('productName')}")
            
            try:
                # Triggers standard legacy generate_ad_image tool
                from agent_tools import execute_tool
                args = {
                    "product_name": prod.get("productName"),
                    "category": prod.get("category", "top"),
                    "style_niche": "streetwear",
                    "ad_format": "editorial"
                }
                # Dry run or live execute
                result = await execute_tool("generate_ad_image", args, mem)
                if result.get("success"):
                    mem.mark_product_processed(prod, ad_paths=result.get("ad_paths", []))
                    print("[LANGGRAPH DESIGNER] Graphic campaign completed successfully.")
                else:
                    print(f"[LANGGRAPH DESIGNER] Graphic campaign failed: {result.get('error')}")
            except Exception as e:
                print(f"[LANGGRAPH ERROR] Designer failed: {e}")
                state["error_list"].append(str(e))
                
    return state


async def copywriter_node(state: AgentState) -> AgentState:
    """Copywriter Node: Generates caption and packages the carousel."""
    print("\n[LANGGRAPH] Copywriter Node active. Formulating product ad copy...")
    mem = Mem0Memory() if Mem0Memory else None
    
    if mem:
        # Check processed but not yet posted
        conn = sqlite3.connect(mem.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE processed_at IS NOT NULL AND posted_at IS NULL")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            prod_name = row[1]
            price = row[4]
            print(f"[LANGGRAPH COPYWRITER] Generating ad copy for {prod_name}...")
            
            try:
                from agent_tools import execute_tool
                args = {
                    "product_name": prod_name,
                    "price_cny": price,
                    "ad_format": "editorial"
                }
                result = await execute_tool("generate_caption", args, mem)
                if result.get("success"):
                    # Mark posted so we know it's finalized
                    mem.mark_product_posted({"id": row[0]}, platform="instagram", post_url="ready")
                    print("[LANGGRAPH COPYWRITER] Ad caption packaged successfully.")
            except Exception as e:
                print(f"[LANGGRAPH ERROR] Copywriter failed: {e}")
                state["error_list"].append(str(e))
                
    return state


# ─── BUILD THE LANGGRAPH ORCHESTRATOR ───

def build_sourcing_graph():
    """Compiles nodes and conditional edges into a stateful StateGraph."""
    if not StateGraph:
        print("[!] LangGraph is not installed. Returning dummy executor.")
        return None
        
    builder = StateGraph(AgentState)
    
    # Add Nodes
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("scout", scout_node)
    builder.add_node("designer", designer_node)
    builder.add_node("copywriter", copywriter_node)
    
    # Entry Point
    builder.set_entry_point("coordinator")
    
    # Conditional Edges Routing
    def router_edge(state: AgentState):
        nxt = state.get("next_step", "wait")
        if nxt in ("scout", "designer", "copywriter"):
            return nxt
        return END  # Pauses or terminates graph execution
        
    builder.add_conditional_edges("coordinator", router_edge)
    
    # Connect leaf nodes back to central coordinator
    builder.add_edge("scout", "coordinator")
    builder.add_edge("designer", "coordinator")
    builder.add_edge("copywriter", "coordinator")
    
    return builder.compile()

# Thread-safe executor
async def run_agentic_workflow():
    """Convenience wrapper to run a single step of the multi-agent graph."""
    graph = build_sourcing_graph()
    if not graph:
        print("[!] LangGraph is offline. Defaulting back to standard autonomous loop.")
        return False
        
    initial_state = {
        "phase": "autonomous",
        "actions_today": 0,
        "current_task": "autonomous_sourcing",
        "next_step": "coordinator",
        "error_list": [],
        "recent_logs": [],
        "context_data": {}
    }
    
    try:
        final_state = await graph.ainvoke(initial_state)
        print(f"[LANGGRAPH RUN COMPLETE] Central State Next Step: {final_state.get('next_step')}")
        return True
    except Exception as e:
        print(f"[LANGGRAPH CRITICAL ERROR] Graph run crashed: {e}")
        return False
