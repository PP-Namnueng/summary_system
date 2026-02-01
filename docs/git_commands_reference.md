# 📚 Git Commands Reference

> Commands you learned on **February 2, 2026**

---

## 🔍 Viewing & Status

| Command | Meaning | When to Use |
|---------|---------|-------------|
| `git status` | Show current state of files | Before any commit to see what changed |
| `git log --oneline -10` | Show last 10 commits (short) | To see your save history |
| `git log` | Show full commit history | Detailed history (press `Q` to exit) |

---

## 💾 Saving Changes

| Command | Meaning | When to Use |
|---------|---------|-------------|
| `git add .` | Stage ALL files for commit | Before committing to prepare files |
| `git add filename` | Stage ONE specific file | When you only want to save one file |
| `git commit -m "message"` | Save staged files with description | After `git add`, creates a save point |
| `git reset` | Unstage all files (undo `git add`) | When you want to redo staging |

---

## ⏪ Undoing Changes

| Command | Meaning | When to Use |
|---------|---------|-------------|
| `git checkout .` | Undo ALL uncommitted changes | Emergency restore to last commit |
| `git checkout -- filename` | Undo changes to ONE file | Restore specific file |
| `git reset --soft HEAD~1` | Undo last commit, keep changes | Made a mistake in commit message |
| `git reset --hard HEAD~1` | Undo last commit, DELETE changes | ⚠️ Dangerous - removes work! |

---

## 🌐 GitHub / Remote

| Command | Meaning | When to Use |
|---------|---------|-------------|
| `git remote add origin URL` | Connect local repo to GitHub | First time setup |
| `git push -u origin main` | Upload code to GitHub | First push to set tracking |
| `git push` | Upload new commits | After first push, shorter command |
| `git push --force` | Overwrite remote with local | When local and remote conflict |

---

## ⚙️ Configuration

| Command | Meaning | When to Use |
|---------|---------|-------------|
| `git config --global user.name "Name"` | Set your name | One-time setup |
| `git config --global user.email "email"` | Set your email | One-time setup |
| `git config --global core.autocrlf true` | Auto-fix line endings | Stop LF/CRLF warnings |

---

## 🌿 Branches (Future Use)

| Command | Meaning | When to Use |
|---------|---------|-------------|
| `git checkout -b branch-name` | Create new branch | Safe experimentation |
| `git checkout main` | Switch to main branch | Return to main code |
| `git merge branch-name` | Combine branch into current | After testing branch works |
| `git branch -d branch-name` | Delete a branch | Clean up after merge |

---

## 📁 .gitignore

**Purpose:** Tell Git which files to ignore (not track)

**Common patterns:**
```
__pycache__/     # Python cache folders
*.pyc            # Compiled Python files
venv/            # Virtual environments
*.mp3            # Audio files
debug_*.txt      # Debug files
library/         # Large data folders
```

---

## 🎯 Your Workflow

```powershell
# 1. Check what changed
git status

# 2. Stage all changes
git add .

# 3. Commit with message
git commit -m "Describe what you did"

# 4. Push to GitHub
git push
```

---

## 🆘 Emergency Commands

```powershell
# Undo ALL changes (back to last commit)
git checkout .

# See what's wrong
git status

# See recent history
git log --oneline -5
```

---

*Keep this file for reference! 🚀*
