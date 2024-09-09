##### Instructions ####
# 1. Install the GitHub CLI: `brew install gh` or https://cli.github.com/
# 2. Run the script: `python3 ./scripts/python/github/create_pr.py base_branch_name`
########################

import os
import subprocess
import sys
from pathlib import Path

## Imports
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# Load .env file if it exists
if os.path.isfile(".env"):
    with open(".env", "r") as file:
        for line in file:
            key, value = line.strip().split("=", 1)
            os.environ[key] = value

print("pushing to remote...")

# Get the current working branch name for the summary
current_branch = (
    subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True)
    .decode()
    .strip()
)

# Push the current branch to the remote
subprocess.run(["git", "push", "--set-upstream", "origin", current_branch])

# Base branch: Use sys.argv[1] if provided, otherwise fall back to EPIC_BRANCH_NAME environment variable
base_branch = "main"

summary = current_branch  # Default summary is the branch name

# Create the pull request using the GitHub CLI
result = subprocess.run(
    [
        "gh",
        "pr",
        "create",
        "--base",
        base_branch,
        "--head",
        current_branch,
        "--title",
        summary,
        "--body",
        "",
    ],
    capture_output=True,
    text=True,  # Ensure output is in text format not bytes
)

# Check if the PR creation was successful
if result.returncode == 0:
    print("Pull request created successfully.")
    subprocess.run(["gh", "pr", "view", "--web"])
else:
    print("Failed to create the pull request.")
    print(result.stderr)
