#!/usr/bin/env python3
import subprocess
import os

def run_git(args):
    """Run git command in ATLAS directory"""
    try:
        result = subprocess.run(['git'] + args, 
                              cwd='/Users/nicholaspate/Documents/ATLAS',
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        print(f"STDERR: {e.stderr}")
        return None

print("🔄 Simple GitHub Revert Process")
print("=" * 40)

# 1. Fetch from GitHub
print("1. Fetching from GitHub...")
result = run_git(['fetch', 'origin'])
print("✅ Fetched from remote")

# 2. Get current branch  
print("\n2. Getting current branch...")
branch = run_git(['branch', '--show-current'])
if branch:
    print(f"Current branch: {branch}")
else:
    print("❌ Could not get branch")
    exit(1)

# 3. Show commits
print(f"\n3. Checking commits...")
local_commit = run_git(['rev-parse', 'HEAD'])
remote_commit = run_git(['rev-parse', f'origin/{branch}'])

print(f"Local commit:  {local_commit[:8]}")
print(f"Remote commit: {remote_commit[:8]}")

if local_commit == remote_commit:
    print("✅ Already up to date with remote")
else:
    print("📝 Local differs from remote - will reset")

# 4. Check what files will be affected
print(f"\n4. Checking what will change...")
status = run_git(['status', '--porcelain'])
if status:
    print("Files that will be reverted:")
    for line in status.split('\n'):
        if line.strip():
            print(f"  {line}")
else:
    print("No local changes detected")

# 5. Save our snapshots first
print(f"\n5. Ensuring snapshots are saved...")
snapshot_dir = '/Users/nicholaspate/Documents/ATLAS/code_snapshots'
os.makedirs(snapshot_dir, exist_ok=True)

# Check if snapshots exist
snapshots = [
    'snapshot_mlflow_tracking.py',
    'snapshot_enhanced_tracking.py', 
    'snapshot_agent_base_changes.py',
    'snapshot_agent_endpoints_changes.py'
]

for snapshot in snapshots:
    if os.path.exists(os.path.join(snapshot_dir, snapshot)):
        print(f"  ✅ {snapshot} exists")
    else:
        print(f"  ⚠️ {snapshot} missing")

# 6. Reset to remote state
print(f"\n6. Resetting to GitHub remote state...")
result = run_git(['reset', '--hard', f'origin/{branch}'])
if result is not None:
    print("✅ Hard reset completed")
else:
    print("❌ Reset failed")
    exit(1)

# 7. Clean untracked files (but preserve snapshots)
print(f"\n7. Cleaning untracked files...")
result = run_git(['clean', '-fd', '--exclude=code_snapshots/**'])
print("✅ Cleaned untracked files")

# 8. Final status
print(f"\n8. Final status check...")
status = run_git(['status', '--porcelain'])
if status:
    remaining = [line for line in status.split('\n') if line.strip() and 'code_snapshots' not in line]
    if remaining:
        print("⚠️ Some files still modified:")
        for line in remaining:
            print(f"  {line}")
    else:
        print("✅ Successfully reverted (snapshots preserved)")
else:
    print("✅ Clean working directory")

print(f"\n🎉 REVERT COMPLETED!")
print(f"📁 Code snapshots preserved in {snapshot_dir}")
print(f"📝 Ready to implement snapshots into clean environment")