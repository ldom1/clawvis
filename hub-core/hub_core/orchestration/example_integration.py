"""
Example: How to use AgentRouter + reverse-prompt in LabOS

This shows how to integrate unified style guide into agent orchestration.
"""

from agent_router import AgentRouter, get_router
from style_guide import load_or_create_style_guide, update_style_guide_from_reverse_prompt


def example_1_basic_routing():
    """Example 1: Basic task routing with unified style."""
    
    # Initialize router with default style guide
    router = AgentRouter()
    
    # Route a task
    task = router.route_task(
        task_id="hub-refresh-001",
        instruction="Generate a system status report",
        agent_id="hub-refresh",
        context="Operational report for Hub status"
    )
    
    print("Routed Task:")
    print(f"  Task ID: {task.task_id}")
    print(f"  Agent: {task.agent_id}")
    print(f"  Instruction with style:\n{task.instruction}")


def example_2_multiple_agents():
    """Example 2: Route tasks to multiple agents with same style."""
    
    router = AgentRouter()
    
    # Multiple tasks for different agents
    tasks = [
        {
            "task_id": "hub-001",
            "instruction": "Monitor system health",
            "agent_id": "hub-refresh",
            "context": "Production system monitoring"
        },
        {
            "task_id": "kanban-001",
            "instruction": "Sync task board",
            "agent_id": "kanban-parser",
            "context": "Daily task synchronization"
        },
        {
            "task_id": "knowledge-001",
            "instruction": "Consolidate knowledge base",
            "agent_id": "knowledge-consolidator",
            "context": "Memory persistence and learning"
        }
    ]
    
    # Route all with same style
    routed_tasks = router.route_multiple_tasks(tasks)
    
    print(f"\nRouted {len(routed_tasks)} tasks with unified style")
    for task in routed_tasks:
        print(f"  ✓ {task.agent_id} ({task.task_id})")


def example_3_custom_style():
    """Example 3: Load or update style guide."""
    
    # Load existing style guide
    style = load_or_create_style_guide(name="default")
    print(f"\nCurrent style guide:")
    print(f"  Name: {style.name}")
    print(f"  Confidence: {style.confidence:.0%}")
    print(f"  Patterns: {', '.join(style.patterns[:2])}")


def example_4_reverse_prompt_update():
    """Example 4: Update style guide using reverse-prompt."""
    
    # Your perfect example
    perfect_report = """## System Status
    
✅ **OPERATIONAL** (15:30:45)

Performance:
- Response time: 145ms (avg)
- Success rate: 99.8%
- Error count: 1/5000

Status: All systems green. Next check at 16:00."""
    
    # Update style from example
    style = update_style_guide_from_reverse_prompt(
        example_text=perfect_report,
        name="operational-reports"
    )
    
    print(f"\nUpdated style guide from example:")
    print(f"  Confidence: {style.confidence:.0%}")
    print(f"  Detected patterns: {style.patterns}")


def example_5_use_global_router():
    """Example 5: Use global router instance."""
    
    # Get global router
    router = get_router()
    
    # Use it everywhere in your app
    task1 = router.route_task(
        task_id="task1",
        instruction="Generate report",
        agent_id="reporter"
    )
    
    task2 = router.route_task(
        task_id="task2",
        instruction="Analyze metrics",
        agent_id="analyzer"
    )
    
    print(f"\nBoth tasks use same style (from global router)")
    print(f"Style confidence: {router.style_guide.confidence:.0%}")


if __name__ == "__main__":
    print("=" * 60)
    print("LabOS AgentRouter + reverse-prompt Examples")
    print("=" * 60)
    
    print("\n1. BASIC ROUTING")
    print("-" * 60)
    example_1_basic_routing()
    
    print("\n2. MULTIPLE AGENTS")
    print("-" * 60)
    example_2_multiple_agents()
    
    print("\n3. CUSTOM STYLE")
    print("-" * 60)
    example_3_custom_style()
    
    print("\n4. REVERSE-PROMPT UPDATE")
    print("-" * 60)
    # example_4_reverse_prompt_update()  # Requires ReversePromptEngine installed
    print("(Skipped: requires ReversePromptEngine)")
    
    print("\n5. GLOBAL ROUTER")
    print("-" * 60)
    example_5_use_global_router()
    
    print("\n" + "=" * 60)
