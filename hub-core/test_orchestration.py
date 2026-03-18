#!/usr/bin/env python3
"""
Test: LabOS orchestration layer with reverse-prompt

Run this to verify the orchestration integration works.
"""

import sys
from pathlib import Path

# Add hub_core to path
sys.path.insert(0, str(Path(__file__).parent))

from hub_core.orchestration import (
    AgentRouter,
    load_or_create_style_guide,
    get_router,
)


def test_1_load_style_guide():
    """Test 1: Load or create default style guide."""
    print("\n🧪 Test 1: Load Style Guide")
    print("=" * 60)
    
    style = load_or_create_style_guide()
    print(f"✅ Loaded style guide: {style.name}")
    print(f"   Confidence: {style.confidence:.0%}")
    print(f"   Patterns: {len(style.patterns)} detected")
    print(f"   Created: {style.created_at[:10]}")


def test_2_basic_routing():
    """Test 2: Route a single task."""
    print("\n🧪 Test 2: Basic Task Routing")
    print("=" * 60)
    
    router = AgentRouter()
    
    task = router.route_task(
        task_id="test-001",
        instruction="Generate a system status report",
        agent_id="test-agent",
        context="Operational monitoring",
    )
    
    print(f"✅ Task routed: {task.task_id}")
    print(f"   Agent: {task.agent_id}")
    print(f"   Priority: {task.priority}")
    print(f"   Instruction with style: {len(task.instruction)} chars")
    print(f"\n   First 150 chars of routed instruction:")
    print(f"   {task.instruction[:150]}...")


def test_3_multiple_agents():
    """Test 3: Route tasks to multiple agents."""
    print("\n🧪 Test 3: Multiple Agents")
    print("=" * 60)
    
    router = AgentRouter()
    
    # Simulate 3 different agents
    agents = ["hub-refresh", "kanban-parser", "knowledge-consolidator"]
    
    tasks = []
    for i, agent_id in enumerate(agents, 1):
        task = router.route_task(
            task_id=f"multi-{i:03d}",
            instruction=f"Execute task for {agent_id}",
            agent_id=agent_id,
        )
        tasks.append(task)
    
    print(f"✅ Routed {len(tasks)} tasks")
    for task in tasks:
        print(f"   • {task.agent_id:25s} (task: {task.task_id})")
    
    print(f"\n   All use same style guide:")
    print(f"   Confidence: {router.style_guide.confidence:.0%}")


def test_4_global_router():
    """Test 4: Use global router instance."""
    print("\n🧪 Test 4: Global Router Instance")
    print("=" * 60)
    
    # Get global router
    router1 = get_router()
    router2 = get_router()
    
    print(f"✅ Retrieved global router instances")
    print(f"   Same instance: {router1 is router2}")
    print(f"   Style name: {router1.style_guide.name}")
    print(f"   Confidence: {router1.style_guide.confidence:.0%}")


def test_5_style_info():
    """Test 5: Get style guide information."""
    print("\n🧪 Test 5: Style Information")
    print("=" * 60)
    
    router = AgentRouter()
    info = router.get_style_info()
    
    print(f"✅ Style guide info:")
    print(f"   Name: {info['name']}")
    print(f"   Use case: {info['use_case']}")
    print(f"   Target audience: {info['target_audience']}")
    print(f"   Confidence: {info['confidence']:.0%}")
    print(f"   Patterns ({len(info['patterns'])}):")
    for pattern in info['patterns'][:3]:
        print(f"      • {pattern}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LabOS Orchestration Tests")
    print("=" * 60)
    
    try:
        test_1_load_style_guide()
        test_2_basic_routing()
        test_3_multiple_agents()
        test_4_global_router()
        test_5_style_info()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
