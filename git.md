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