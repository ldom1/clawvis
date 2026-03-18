"""LabOS Agent Router — Route tasks through agents with unified style guide."""

from dataclasses import dataclass
from typing import Dict, Optional, Any
from loguru import logger

from .style_guide import StyleGuide, load_or_create_style_guide


@dataclass
class TaskConfig:
    """Configuration for task routing."""
    
    task_id: str
    instruction: str
    agent_id: str
    priority: str = "normal"
    context: str = ""
    timeout_seconds: int = 300
    
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "instruction": self.instruction,
            "agent_id": self.agent_id,
            "priority": self.priority,
            "context": self.context,
            "timeout_seconds": self.timeout_seconds,
        }


class AgentRouter:
    """Routes tasks through agents with unified style guide."""
    
    def __init__(self, style_guide: Optional[StyleGuide] = None):
        """Initialize router with style guide."""
        if style_guide is None:
            style_guide = load_or_create_style_guide()
        
        self.style_guide = style_guide
        self.logger = logger.bind(component="agent-router")
        
        self.logger.info(
            f"AgentRouter initialized with style guide",
            style_name=style_guide.name,
            confidence=style_guide.confidence,
        )
    
    def route_task(
        self,
        task_id: str,
        instruction: str,
        agent_id: str,
        context: str = "",
        priority: str = "normal",
        apply_style: bool = True,
    ) -> TaskConfig:
        """
        Route a task through an agent with unified style.
        
        Args:
            task_id: Unique task identifier
            instruction: What the agent should do
            agent_id: Which agent to use
            context: Additional context
            priority: Task priority (low, normal, high)
            apply_style: Whether to apply style guide (default: True)
        
        Returns:
            TaskConfig with routed instruction
        """
        
        # Apply style guide to instruction
        if apply_style:
            enhanced_instruction = self._apply_style_to_instruction(
                instruction,
                context,
            )
        else:
            enhanced_instruction = instruction
        
        config = TaskConfig(
            task_id=task_id,
            instruction=enhanced_instruction,
            agent_id=agent_id,
            priority=priority,
            context=context,
        )
        
        self.logger.info(
            "Task routed",
            task_id=task_id,
            agent_id=agent_id,
            priority=priority,
            style_applied=apply_style,
        )
        
        return config
    
    def route_multiple_tasks(
        self,
        tasks: list[Dict[str, str]],
        apply_style: bool = True,
    ) -> list[TaskConfig]:
        """Route multiple tasks."""
        routed = []
        for task in tasks:
            config = self.route_task(
                task_id=task.get("task_id", ""),
                instruction=task.get("instruction", ""),
                agent_id=task.get("agent_id", ""),
                context=task.get("context", ""),
                priority=task.get("priority", "normal"),
                apply_style=apply_style,
            )
            routed.append(config)
        
        return routed
    
    def _apply_style_to_instruction(
        self,
        instruction: str,
        context: str = "",
    ) -> str:
        """Apply style guide to instruction."""
        
        context_section = f"\n\nContext: {context}" if context else ""
        
        return f"""{instruction}

---

**Output Style Guide:**

{self.style_guide.prompt}{context_section}

(Confidence: {self.style_guide.confidence:.0%})"""
    
    def get_style_info(self) -> Dict[str, Any]:
        """Get style guide information."""
        return {
            "name": self.style_guide.name,
            "prompt": self.style_guide.prompt,
            "patterns": self.style_guide.patterns,
            "confidence": self.style_guide.confidence,
            "use_case": self.style_guide.use_case,
            "target_audience": self.style_guide.target_audience,
        }
    
    def update_style_guide(
        self,
        example_text: str,
        reverse_prompt_engine=None,
    ) -> StyleGuide:
        """Update style guide from reverse-prompt example."""
        from .style_guide import update_style_guide_from_reverse_prompt
        
        self.style_guide = update_style_guide_from_reverse_prompt(
            example_text,
            name=self.style_guide.name,
            reverse_prompt_engine=reverse_prompt_engine,
        )
        
        self.logger.info(
            "Style guide updated from reverse-prompt",
            confidence=self.style_guide.confidence,
            patterns=len(self.style_guide.patterns),
        )
        
        return self.style_guide


# Global router instance
_router: Optional[AgentRouter] = None


def get_router(style_guide: Optional[StyleGuide] = None) -> AgentRouter:
    """Get or create global router instance."""
    global _router
    if _router is None:
        _router = AgentRouter(style_guide)
    return _router


def reset_router():
    """Reset global router instance."""
    global _router
    _router = None
