#!/usr/bin/env python3
"""
Script to revert to last GitHub commit state using remote server
"""
import subprocess
import os
import sys

def run_command(cmd, description=""):
    """Run command and return result."""
    try:
        print(f"Running: {' '.join(cmd)} {description}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/Users/nicholaspate/Documents/ATLAS')
        if result.returncode != 0:
            print(f"⚠️ Command warning/error: {result.stderr}")
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("🔄 REVERTING TO LAST GITHUB COMMIT STATE")
    print("=" * 50)
    
    # 1. Fetch latest from GitHub remote
    print("1. Fetching latest from GitHub remote...")
    stdout, stderr, returncode = run_command(['git', 'fetch', 'origin'], "(fetch from GitHub)")
    
    if returncode != 0:
        print(f"❌ Failed to fetch from remote: {stderr}")
        return False
    
    # 2. Check current branch
    print("\n2. Checking current branch...")
    stdout, stderr, returncode = run_command(['git', 'branch', '--show-current'])
    
    if returncode != 0:
        print(f"❌ Failed to get current branch: {stderr}")
        return False
    
    current_branch = stdout.strip()
    print(f"   Current branch: {current_branch}")
    
    # 3. Show what we're reverting from and to
    print("\n3. Showing commit comparison...")
    
    # Current local commit
    stdout, stderr, returncode = run_command(['git', 'log', '--oneline', '-1'])
    if returncode == 0:
        print(f"   Local HEAD: {stdout.strip()}")
    
    # Remote commit
    stdout, stderr, returncode = run_command(['git', 'log', '--oneline', '-1', f'origin/{current_branch}'])
    if returncode == 0:
        print(f"   Remote HEAD: {stdout.strip()}")
    
    # 4. Stash any local changes to preserve our snapshots
    print("\n4. Stashing local changes...")
    stdout, stderr, returncode = run_command(['git', 'stash', 'push', '-m', 'Pre-revert stash', '--include-untracked'])
    
    if returncode != 0:
        print(f"⚠️ Stash warning: {stderr}")
    else:
        print(f"✅ Stashed changes: {stdout.strip()}")
    
    # 5. Hard reset to remote GitHub state
    print("\n5. Hard reset to GitHub remote state...")
    stdout, stderr, returncode = run_command(['git', 'reset', '--hard', f'origin/{current_branch}'])
    
    if returncode != 0:
        print(f"❌ Hard reset failed: {stderr}")
        return False
    
    print(f"✅ Reset to remote: {stdout.strip()}")
    
    # 6. Clean any remaining untracked files
    print("\n6. Cleaning untracked files...")
    stdout, stderr, returncode = run_command(['git', 'clean', '-fd'])
    
    if returncode != 0:
        print(f"⚠️ Clean warning: {stderr}")
    
    # 7. Restore our snapshots from stash (selectively)
    print("\n7. Restoring snapshots...")
    
    # Create code_snapshots directory
    os.makedirs('/Users/nicholaspate/Documents/ATLAS/code_snapshots', exist_ok=True)
    
    # Try to restore just our snapshot files from stash
    snapshot_files = [
        'code_snapshots/snapshot_mlflow_tracking.py',
        'code_snapshots/snapshot_enhanced_tracking.py', 
        'code_snapshots/snapshot_agent_base_changes.py',
        'code_snapshots/snapshot_agent_endpoints_changes.py'
    ]
    
    for file_path in snapshot_files:
        stdout, stderr, returncode = run_command(['git', 'show', 'stash@{0}:' + file_path])
        if returncode == 0:
            # Write the file content
            full_path = f'/Users/nicholaspate/Documents/ATLAS/{file_path}'
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(stdout)
            print(f"   ✅ Restored {file_path}")
        else:
            print(f"   ⚠️ Could not restore {file_path}: {stderr}")
    
    # 8. Verify final state
    print("\n8. Verifying final state...")
    stdout, stderr, returncode = run_command(['git', 'status'])
    
    if returncode != 0:
        print(f"❌ Status check failed: {stderr}")
        return False
    
    print("✅ Git status after revert:")
    print(stdout)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ GITHUB REVERT FAILED - Check errors above")
        sys.exit(1)
    else:
        print("\n🎉 SUCCESSFULLY REVERTED TO GITHUB STATE")
        print("📁 Code snapshots preserved in code_snapshots/ directory")
        print("📝 You can now implement the snapshots back into the clean environment")
        sys.exit(0)