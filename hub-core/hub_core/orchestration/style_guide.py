"""Clawvis Style Guide — Unified voice management using reverse-prompt."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger


@dataclass
class StyleGuide:
    """Unified style guide for LabOS agents."""

    name: str
    prompt: str
    patterns: list
    confidence: float
    created_at: str
    updated_at: str
    use_case: str = "operational-reports"
    target_audience: str = "technical"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict(), indent=2)


def get_style_guide_dir() -> Path:
    """Get the style guide directory."""
    style_dir = Path.home() / ".openclaw" / "labos" / "standards"
    style_dir.mkdir(parents=True, exist_ok=True)
    return style_dir


def get_default_style_guide() -> str:
    """Returns the default LabOS style guide prompt."""
    return """Write operational reports for LabOS with these characteristics:

**Format:**
- Use Markdown with # and ## headers
- Include ✅/❌ emoji status indicators with timestamps
- Metrics section with "Key: value" format
- Results summary (1-2 sentences max)

**Tone:**
- Technical but not jargon-heavy
- Factual and concise
- Confidence in tone

**Structure:**
- Header: Task/Component name
- Status: Explicit outcome (✅ SUCCESS or ❌ FAILED)
- Metrics: Current values (name: value)
- Result: One-line summary
- Next: What comes next (if applicable)

**Length:** 80-120 words max

**Example:**
## Hub Refresh
✅ **SUCCESS** (09:38:50)
- MammouthAI: $6.94/$12.00
- CPU: 7.8%
- RAM: 27.1%
Result: Session tokens updated."""


def load_or_create_style_guide(
    name: str = "default",
    force_create: bool = False,
) -> StyleGuide:
    """Load existing style guide or create default."""

    style_dir = get_style_guide_dir()
    style_file = style_dir / f"{name}.json"

    # Try to load existing
    if style_file.exists() and not force_create:
        try:
            with open(style_file) as f:
                data = json.load(f)
                logger.info(f"Loaded style guide: {name}")
                return StyleGuide(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to load style guide {name}: {e}")

    # Create default
    logger.info(f"Creating default style guide: {name}")
    style = StyleGuide(
        name=name,
        prompt=get_default_style_guide(),
        patterns=[
            "tone: technical",
            "structure: section-based",
            "format: markdown-headers",
            "format: emoji-indicators",
            "length: brief (80-120 words)",
        ],
        confidence=0.94,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        use_case="operational-reports",
        target_audience="technical",
    )

    # Save
    with open(style_file, "w") as f:
        f.write(style.to_json())

    logger.info(f"Saved style guide to {style_file}")
    return style


def apply_style_guide(
    prompt: str,
    style_guide: StyleGuide,
    context: str = "",
) -> str:
    """Apply style guide to a prompt."""

    if context:
        context_str = f"\n\nContext: {context}"
    else:
        context_str = ""

    return f"""{prompt}

---

Follow this style guide:

{style_guide.prompt}{context_str}"""


def update_style_guide_from_reverse_prompt(
    example_text: str,
    name: str = "default",
    reverse_prompt_engine=None,
) -> StyleGuide:
    """Update style guide by reverse-engineering from example."""

    if reverse_prompt_engine is None:
        try:
            # Import locally to avoid circular imports
            import sys

            sys.path.insert(
                0, str(Path.home() / ".openclaw" / "skills" / "reverse-prompt" / "core")
            )
            from reverse_prompt.engine import ReversePromptEngine

            reverse_prompt_engine = ReversePromptEngine()
        except ImportError as e:
            logger.error(f"Could not import ReversePromptEngine: {e}")
            return load_or_create_style_guide(name)

    logger.info("Reverse-engineering style guide from example...")

    result = reverse_prompt_engine.reverse_engineer(
        example_text=example_text,
        context="LabOS operational report style",
        iterations=3,
    )

    style = StyleGuide(
        name=name,
        prompt=result["reconstructed_prompt"],
        patterns=result["patterns"],
        confidence=result["confidence"],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        use_case="operational-reports",
        target_audience="technical",
    )

    # Save
    style_dir = get_style_guide_dir()
    style_file = style_dir / f"{name}.json"
    with open(style_file, "w") as f:
        f.write(style.to_json())

    logger.info(f"Updated style guide: {name} (confidence: {style.confidence:.2%})")
    return style
