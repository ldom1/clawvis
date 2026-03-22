#!/usr/bin/env bash
# reverse-prompt skill — Entry point
# Reverse-engineer prompts from example outputs

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"

# Defaults
MODEL="${MODEL:-claude-haiku}"
ITERATIONS="${ITERATIONS:-3}"
CONFIDENCE_THRESHOLD="${CONFIDENCE_THRESHOLD:-0.85}"

# Parse arguments
EXAMPLE_TEXT=""
CONTEXT=""
MODE="cli"

while [[ $# -gt 0 ]]; do
  case $1 in
    --example)
      EXAMPLE_TEXT="$2"
      shift 2
      ;;
    --context)
      CONTEXT="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --iterations)
      ITERATIONS="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate
if [[ -z "$EXAMPLE_TEXT" ]]; then
  echo "Usage: $0 --example '<text>' [--context '<context>'] [--model <model>] [--iterations <n>]"
  echo ""
  echo "Example:"
  echo "  $0 --example 'Write a 300-word vision statement' --model claude-haiku --iterations 3"
  exit 1
fi

# Run Python engine
export PYTHONPATH="$CORE_DIR:$PYTHONPATH"

python3 << 'PYTHON_SCRIPT'
import sys
import json
import os

# Add core to path
sys.path.insert(0, os.environ.get("PYTHONPATH", "").split(":")[0])

from reverse_prompt.engine import ReversePromptEngine

# Get args from environment (passed from bash)
example_text = os.environ.get("EXAMPLE_TEXT", "")
context = os.environ.get("CONTEXT", "")
model = os.environ.get("MODEL", "claude-haiku")
iterations = int(os.environ.get("ITERATIONS", "3"))
mode = os.environ.get("MODE", "cli")

# Run engine
engine = ReversePromptEngine(model=model, iterations=iterations)

try:
    result = engine.reverse_engineer(
        example_text=example_text,
        context=context,
        iterations=iterations
    )
    
    if mode == "json":
        # Output JSON for API consumption
        print(json.dumps(result, indent=2))
    else:
        # CLI output
        print("\n" + "="*60)
        print("REVERSE PROMPT RESULT")
        print("="*60)
        print(f"\n📝 Reconstructed Prompt:\n")
        print(result["reconstructed_prompt"])
        print(f"\n\n📊 Confidence: {result['confidence']:.2%}")
        print(f"Iterations used: {result['iterations_used']}")
        
        if result["patterns"]:
            print(f"\n🎯 Detected Patterns:")
            for pattern in result["patterns"]:
                print(f"  • {pattern}")
        
        print("\n" + "="*60 + "\n")
        
except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
