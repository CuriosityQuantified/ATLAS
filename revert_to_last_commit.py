#!/usr/bin/env python3
"""
Script to safely revert to last GitHub commit state
"""
import subprocess
import os
import sys

def run_command(cmd):
    """Run command and return result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/Users/nicholaspate/Documents/ATLAS')
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("🔄 REVERTING TO LAST GITHUB COMMIT STATE")
    print("=" * 50)
    
    # First, check current status
    print("1. Checking current git status...")
    stdout, stderr, returncode = run_command(['git', 'status', '--porcelain'])
    
    if returncode != 0:
        print(f"❌ Git status failed: {stderr}")
        return False
    
    if stdout.strip():
        print("📝 Found modified files:")
        for line in stdout.strip().split('\n'):
            print(f"   {line}")
    else:
        print("✅ No changes to revert")
        return True
    
    # Show what we're reverting from
    print("\n2. Current commit:")
    stdout, stderr, returncode = run_command(['git', 'log', '--oneline', '-1'])
    if returncode == 0:
        print(f"   {stdout.strip()}")
    
    # Reset all changes to last commit
    print("\n3. Reverting all changes...")
    
    # Reset any staged changes
    stdout, stderr, returncode = run_command(['git', 'reset', 'HEAD'])
    if returncode != 0:
        print(f"⚠️ Reset HEAD warning: {stderr}")
    
    # Discard all working directory changes
    stdout, stderr, returncode = run_command(['git', 'checkout', '--', '.'])
    if returncode != 0:
        print(f"❌ Checkout failed: {stderr}")
        return False
    
    # Clean any untracked files (but keep our snapshots)
    stdout, stderr, returncode = run_command(['git', 'clean', '-fd', '--exclude=code_snapshots/**', '--exclude=check_git_status.py', '--exclude=revert_to_last_commit.py'])
    if returncode != 0:
        print(f"⚠️ Clean warning: {stderr}")
    
    # Verify the revert
    print("\n4. Verifying revert...")
    stdout, stderr, returncode = run_command(['git', 'status', '--porcelain'])
    
    if returncode != 0:
        print(f"❌ Status check failed: {stderr}")
        return False
    
    remaining_changes = [line for line in stdout.strip().split('\n') if line.strip() and not any(x in line for x in ['code_snapshots', 'check_git_status.py', 'revert_to_last_commit.py'])]
    
    if remaining_changes:
        print("⚠️ Some files still modified:")
        for line in remaining_changes:
            print(f"   {line}")
    else:
        print("✅ Successfully reverted to last commit state")
        print("📁 Preserved snapshots in code_snapshots/ directory")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ REVERT FAILED - Check errors above")
        sys.exit(1)
    else:
        print("\n🎉 REVERT COMPLETED SUCCESSFULLY")
        sys.exit(0)