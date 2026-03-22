#!/bin/bash
# test_example.sh — Simple test of reverse-prompt skill

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🧪 Testing reverse-prompt skill..."
echo ""

# Example 1: LabOS Report
echo "📋 Test 1: LabOS Operational Report"
echo "======================================"

LABOS_REPORT=$(cat << 'EOF'
## Hub Refresh Summary

✅ **SUCCESS** — 09:38:50

### Metrics
- MammouthAI: $6.94 / $12.00 (58% remaining)
- CPU: 7.8%
- RAM: 27.1% (2.06 GB / 7.6 GB)
- Disk: 34.0%

### Result
Session tokens updated from API. OpenClaw status check timed out (non-blocking).
EOF
)

echo "Example text:"
echo "$LABOS_REPORT"
echo ""
echo "Running reverse-prompt..."

bash "$SCRIPT_DIR/scripts/run.sh" \
  --example "$LABOS_REPORT" \
  --model claude-haiku \
  --iterations 2

echo ""
echo "✅ Test 1 Complete"
echo ""

# Example 2: Brief style
echo "📋 Test 2: Concise Technical Summary"
echo "======================================"

TECH_SUMMARY=$(cat << 'EOF'
Integration complete. 
Status: Ready for production.
Next: Deploy Loki stack (ETA: Apr 26).
EOF
)

echo "Example text:"
echo "$TECH_SUMMARY"
echo ""
echo "Running reverse-prompt..."

bash "$SCRIPT_DIR/scripts/run.sh" \
  --example "$TECH_SUMMARY" \
  --context "DevOps runbook" \
  --model claude-haiku \
  --iterations 1

echo ""
echo "✅ Test 2 Complete"
echo ""

echo "🎉 All tests passed!"
echo ""
echo "📚 Next: Read EXAMPLES.md for production use cases"
