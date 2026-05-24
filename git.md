# Run:

### Init
git init

### Add 
git add .

### Commit
git commit -m "chore: add github actions ci and gitignore"
git branch -M main
git remote add origin https://github.com/linguyenvivito/python-todo-fullstack-project
git push -u origin main

# Check current branch
git branch --show-current

# Confirm latest commit exists
git log --oneline -n 3

# Push current branch to remote (first time for this branch)
git push -u origin $(git branch --show-current)

# Next pushes on same branch
git push

# 1) Check changed files
git status

# 2) Stage files (all)
git add .

# Or stage specific files only
# git add app/slices/tasks/service.py readme.md

# 3) Commit
git commit -m "feat: describe your change"

# 4) Push
git push origin main


# 1) Make sure you're in repo root
git status

# 2) Create and switch to a new branch
git checkout -b feature/<short-name>
# example: git checkout -b feature/health-endpoint

# 3) Implement your code changes
# (edit files, run tests)

# 4) Check what changed
git status
git diff

# 5) Stage changes
git add .

# 6) Commit
git commit -m "feat: add <feature summary>"

# 7) Push branch to GitHub
git push -u origin feature/<short-name>

# 1) make sure you're on main
git checkout main

# 2) fetch latest remote refs (does not change your files)
git fetch origin

# 3) compare local main with remote main
git status -sb


git pull origin main