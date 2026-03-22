"""
ReversePromptEngine: RPEGA (Reverse Prompt Engineering Genetic Algorithm)

Reconstructs optimal prompts from example outputs using iterative optimization.
"""

import re
import json
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import anthropic
import os


@dataclass
class ReversePromptResult:
    """Result of reverse prompt engineering."""
    reconstructed_prompt: str
    confidence: float
    patterns: List[str]
    iterations_used: int
    metadata: Dict[str, Any] = None


class ReversePromptEngine:
    """
    Reverse-engineer prompts from example outputs.
    
    Algorithm: RPEGA (Reverse Prompt Engineering Genetic Algorithm)
    - Initialize: Generate 5 candidate prompts from example
    - Iterate: Score, mutate, refine based on output similarity
    - Converge: Return best prompt with confidence score
    """
    
    def __init__(
        self,
        model: str = "claude-haiku",
        iterations: int = 3,
        confidence_threshold: float = 0.85,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the engine.
        
        Args:
            model: "claude-haiku" or "claude-opus"
            iterations: Number of refinement iterations (1-10)
            confidence_threshold: Minimum confidence for output (0-1)
            api_key: Anthropic API key (defaults to env var)
        """
        self.model = model
        self.iterations = min(max(iterations, 1), 10)
        self.confidence_threshold = confidence_threshold
        
        # Initialize Anthropic client
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def reverse_engineer(
        self,
        example_text: str,
        context: str = "",
        iterations: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Reverse-engineer the optimal prompt for generating this example.
        
        Args:
            example_text: The finished output/example to analyze
            context: Optional context (e.g., "Target: CTOs", "LabOS report")
            iterations: Override default iterations for this run
        
        Returns:
            Dictionary with:
                - reconstructed_prompt: str
                - confidence: float (0-1)
                - patterns: list of detected patterns
                - iterations_used: int
                - metadata: additional details
        """
        iterations = iterations or self.iterations
        
        # Step 1: Detect patterns in example
        patterns = self._detect_patterns(example_text)
        
        # Step 2: Generate initial candidates
        candidates = self._generate_initial_candidates(example_text, context, patterns)
        
        # Step 3: Iterative refinement (RPEGA)
        best_candidate = self._refine_candidates(example_text, candidates, iterations)
        
        # Step 4: Calculate confidence
        confidence = self._calculate_confidence(best_candidate, example_text, patterns)
        
        return {
            "reconstructed_prompt": best_candidate,
            "confidence": confidence,
            "patterns": patterns,
            "iterations_used": iterations,
        }
    
    def _detect_patterns(self, text: str) -> List[str]:
        """Detect structural patterns in the example text."""
        patterns = []
        
        # Tone detection
        tone_indicators = {
            "technical": r"(algorithm|implementation|API|database|schema)",
            "conversational": r"(we|you|I|let's|actually)",
            "formal": r"(therefore|furthermore|respectively)",
            "inspirational": r"(transform|future|vision|powerful|amazing)",
        }
        
        for tone, regex in tone_indicators.items():
            if re.search(regex, text, re.IGNORECASE):
                patterns.append(f"tone: {tone}")
        
        # Structure detection
        if text.count("\n") > 10:
            patterns.append("structure: detailed/multi-section")
        elif text.count("\n") > 3:
            patterns.append("structure: section-based")
        else:
            patterns.append("structure: concise/single-block")
        
        # Format detection
        if "#" in text:
            patterns.append("format: markdown-headers")
        if "```" in text:
            patterns.append("format: code-blocks")
        if "- " in text or "* " in text:
            patterns.append("format: bullet-list")
        if "{" in text and "}" in text:
            patterns.append("format: json-like")
        
        # Length pattern
        word_count = len(text.split())
        if word_count < 50:
            patterns.append("length: brief (<50 words)")
        elif word_count < 300:
            patterns.append("length: medium (50-300 words)")
        else:
            patterns.append("length: detailed (>300 words)")
        
        # Emoji/formatting
        if "✅" in text or "❌" in text or "🎯" in text:
            patterns.append("format: emoji-indicators")
        
        return patterns
    
    def _generate_initial_candidates(
        self,
        example_text: str,
        context: str,
        patterns: List[str],
    ) -> List[str]:
        """Generate 5 initial prompt candidates."""
        
        context_str = f"\nContext: {context}" if context else ""
        patterns_str = "\n".join([f"- {p}" for p in patterns])
        
        prompt = f"""Given this example output, generate 5 different prompts that could produce it.

EXAMPLE OUTPUT:
{example_text}

DETECTED PATTERNS:
{patterns_str}{context_str}

Generate 5 DISTINCT prompt variations that would create similar output.
Return as JSON array with key "prompts".

Format:
{{"prompts": ["Prompt 1...", "Prompt 2...", ...]}}

Make each prompt different in approach but all would generate similar output style/tone."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(response.content[0].text)
            return result.get("prompts", [])[:5]
        except (json.JSONDecodeError, IndexError):
            # Fallback: use the full response as a single prompt
            return [response.content[0].text]
    
    def _refine_candidates(
        self,
        example_text: str,
        candidates: List[str],
        iterations: int,
    ) -> str:
        """Refine candidates using genetic algorithm approach."""
        
        current_best = candidates[0] if candidates else ""
        
        for iteration in range(iterations):
            # Score each candidate
            scores = []
            for candidate in candidates:
                score = self._score_candidate(candidate, example_text)
                scores.append((candidate, score))
            
            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)
            current_best = scores[0][0]
            
            # Generate new variants from top performers
            if iteration < iterations - 1:
                top_candidates = [s[0] for s in scores[:2]]
                new_variants = self._mutate_candidates(top_candidates, example_text)
                candidates = [s[0] for s in scores[:3]] + new_variants[:2]
        
        return current_best
    
    def _score_candidate(self, candidate: str, example_text: str) -> float:
        """Score how well this prompt would generate the example."""
        
        # Simple heuristic scoring
        score = 0.0
        
        # Check for key structural elements
        candidate_lower = candidate.lower()
        example_lower = example_text.lower()
        
        # Word overlap (ROUGE-1 style)
        candidate_words = set(candidate_lower.split())
        example_words = set(example_lower.split())
        
        if example_words:
            overlap = len(candidate_words & example_words) / len(example_words)
            score += overlap * 0.4
        
        # Check for relevant instructions
        if any(word in candidate_lower for word in ["format", "structure", "tone", "style"]):
            score += 0.3
        
        # Check for audience/context awareness
        if any(word in candidate_lower for word in ["target", "audience", "user", "reader"]):
            score += 0.2
        
        # Penalize overly generic prompts
        if len(candidate) < 30:
            score *= 0.5
        
        return min(score, 1.0)
    
    def _mutate_candidates(self, top_candidates: List[str], example_text: str) -> List[str]:
        """Generate variations of top candidates."""
        
        candidates_str = "\n".join([f"- {c}" for c in top_candidates])
        
        prompt = f"""These two prompts are performing well for generating this output:

{candidates_str}

OUTPUT EXAMPLE:
{example_text}

Generate 2 NEW prompt variations that combine the strengths of both.
Return as JSON: {{"prompts": ["New 1...", "New 2..."]}}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            result = json.loads(response.content[0].text)
            return result.get("prompts", [])[:2]
        except (json.JSONDecodeError, IndexError):
            return []
    
    def _calculate_confidence(
        self,
        prompt: str,
        example_text: str,
        patterns: List[str],
    ) -> float:
        """Calculate confidence score (0-1)."""
        
        score = 0.5  # Base score
        
        # Prompt quality checks
        if 50 < len(prompt) < 5000:
            score += 0.15  # Reasonable length
        
        if any(word in prompt.lower() for word in ["format", "tone", "structure"]):
            score += 0.15  # Contains instruction keywords
        
        # Pattern coverage
        if patterns:
            score += 0.2  # Patterns detected means more confidence
        
        return min(score, 0.99)


# Utility: Simple example for testing
if __name__ == "__main__":
    example = """
    # Hub Refresh Report
    
    ✅ SUCCESS
    
    Metrics:
    - MammouthAI: $6.94/$12.00
    - CPU: 7.8%
    - RAM: 27.1%
    """
    
    engine = ReversePromptEngine()
    result = engine.reverse_engineer(example)
    
    print(f"Prompt: {result['reconstructed_prompt']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Patterns: {result['patterns']}")
