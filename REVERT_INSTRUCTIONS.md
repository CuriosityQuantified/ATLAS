# GitHub Revert Instructions

## Quick Revert to Last GitHub Commit

Since we're experiencing shell session issues with the Bash tool, here are the manual steps to revert to the last GitHub commit state:

### Option 1: Command Line (Manual Execution)

Open Terminal and run these commands in sequence:

```bash
cd /Users/nicholaspate/Documents/ATLAS

# 1. Fetch latest from GitHub
git fetch origin

# 2. Check current branch
git branch --show-current

# 3. See what will be reverted
git status

# 4. Hard reset to GitHub remote state (replace 'main' with your actual branch)
git reset --hard origin/main

# 5. Clean any untracked files (preserving snapshots)
git clean -fd --exclude=code_snapshots/**

# 6. Verify clean state
git status
```

### Option 2: Backup Approach - Manual File Restoration

If git commands are problematic, you can manually restore the original files by:

1. **Delete the modified MLflow files:**
   ```bash
   rm -f backend/src/mlflow/tracking.py
   rm -f backend/src/mlflow/enhanced_tracking.py
   ```

2. **Revert agent files to original state:**
   - Restore `backend/src/agents/base.py` without the mlflow_tracker parameter
   - Restore `backend/src/agents/global_supervisor.py` without mlflow_tracker parameter  
   - Restore `backend/src/agents/library.py` without mlflow_tracker parameter
   - Restore `backend/src/api/agent_endpoints.py` without MLflow integration

### What Files Need to be Reverted

Based on our snapshots, these are the main files that were modified:

1. **Created Files (DELETE these):**
   - `backend/src/mlflow/tracking.py`
   - `backend/src/mlflow/enhanced_tracking.py`

2. **Modified Files (REVERT these):**
   - `backend/src/agents/base.py` - Remove mlflow_tracker parameter and related code
   - `backend/src/agents/global_supervisor.py` - Remove mlflow_tracker parameter
   - `backend/src/agents/library.py` - Remove mlflow_tracker parameter  
   - `backend/src/api/agent_endpoints.py` - Remove MLflow integration code

3. **Preserve These:**
   - `code_snapshots/` directory and all files within
   - All test files
   - Documentation files

### After Revert

Once reverted to the clean GitHub state:

1. **Verify the revert:**
   ```bash
   git status  # Should show clean working directory
   ```

2. **Confirm snapshots preserved:**
   ```bash
   ls code_snapshots/
   # Should show:
   # - snapshot_mlflow_tracking.py
   # - snapshot_enhanced_tracking.py  
   # - snapshot_agent_base_changes.py
   # - snapshot_agent_endpoints_changes.py
   ```

3. **Ready for Step 3:** Implement snapshots back into clean environment

## Why This Approach

- **Clean slate**: Ensures we start from a known good state
- **Preserves work**: Our snapshots contain all the MLflow integration code
- **Controlled implementation**: We can add back the features piece by piece
- **Testing friendly**: Each piece can be tested individually

## Next Steps

After successful revert, we'll implement the snapshots with any necessary modifications for the clean environment.