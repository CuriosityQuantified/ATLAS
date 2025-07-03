#!/bin/bash

echo "🔄 REVERTING TO LAST GITHUB COMMIT STATE"
echo "=================================================="

cd /Users/nicholaspate/Documents/ATLAS

echo "1. Fetching from GitHub remote..."
git fetch origin

echo "2. Getting current branch..."
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

echo "3. Showing current state..."
echo "Local HEAD:"
git log --oneline -1

echo "Remote HEAD:"
git log --oneline -1 origin/$CURRENT_BRANCH

echo "4. Stashing local changes (including our snapshots)..."
git stash push -m "Pre-revert stash with snapshots" --include-untracked

echo "5. Hard reset to GitHub remote state..."
git reset --hard origin/$CURRENT_BRANCH

echo "6. Cleaning any remaining files..."
git clean -fd

echo "7. Creating snapshots directory..."
mkdir -p code_snapshots

echo "8. Restoring snapshot files from stash..."
git show stash@{0}:code_snapshots/snapshot_mlflow_tracking.py > code_snapshots/snapshot_mlflow_tracking.py 2>/dev/null && echo "✅ Restored snapshot_mlflow_tracking.py" || echo "⚠️ Could not restore snapshot_mlflow_tracking.py"

git show stash@{0}:code_snapshots/snapshot_enhanced_tracking.py > code_snapshots/snapshot_enhanced_tracking.py 2>/dev/null && echo "✅ Restored snapshot_enhanced_tracking.py" || echo "⚠️ Could not restore snapshot_enhanced_tracking.py"

git show stash@{0}:code_snapshots/snapshot_agent_base_changes.py > code_snapshots/snapshot_agent_base_changes.py 2>/dev/null && echo "✅ Restored snapshot_agent_base_changes.py" || echo "⚠️ Could not restore snapshot_agent_base_changes.py"

git show stash@{0}:code_snapshots/snapshot_agent_endpoints_changes.py > code_snapshots/snapshot_agent_endpoints_changes.py 2>/dev/null && echo "✅ Restored snapshot_agent_endpoints_changes.py" || echo "⚠️ Could not restore snapshot_agent_endpoints_changes.py"

echo "9. Final verification..."
echo "Git status:"
git status

echo ""
echo "🎉 GITHUB REVERT COMPLETED!"
echo "📁 Snapshots preserved in code_snapshots/ directory"
echo "📝 Ready to implement snapshots back into clean environment"