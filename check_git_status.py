#!/usr/bin/env python3
import subprocess
import os
import sys

os.chdir('/Users/nicholaspate/Documents/ATLAS')

def run_git_command(cmd):
    """Run git command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

# Check git status
print("=== CHECKING GIT STATUS ===")
stdout, stderr, returncode = run_git_command(['git', 'status', '--porcelain'])
if returncode == 0:
    if stdout.strip():
        print("Modified files:")
        print(stdout)
    else:
        print("No changes detected")
else:
    print(f"Error: {stderr}")

print("\n=== RECENT COMMITS ===")
stdout, stderr, returncode = run_git_command(['git', 'log', '--oneline', '-3'])
if returncode == 0:
    print(stdout)
else:
    print(f"Error: {stderr}")

print("\n=== CURRENT BRANCH ===")
stdout, stderr, returncode = run_git_command(['git', 'branch', '--show-current'])
if returncode == 0:
    print(f"Current branch: {stdout.strip()}")
else:
    print(f"Error: {stderr}")

print("\n=== CHECKING FOR STAGED CHANGES ===")
stdout, stderr, returncode = run_git_command(['git', 'diff', '--cached', '--name-only'])
if returncode == 0:
    if stdout.strip():
        print("Staged files:")
        print(stdout)
    else:
        print("No staged changes")
else:
    print(f"Error: {stderr}")

print("\n=== CHECKING FOR UNSTAGED CHANGES ===")
stdout, stderr, returncode = run_git_command(['git', 'diff', '--name-only'])
if returncode == 0:
    if stdout.strip():
        print("Unstaged files:")
        print(stdout)
    else:
        print("No unstaged changes")
else:
    print(f"Error: {stderr}")