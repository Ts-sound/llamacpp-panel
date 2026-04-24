# GitHub Actions Release Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add GitHub Actions workflow to automatically build and release Windows EXE when pushing version tags.

**Architecture:** Single workflow file triggered by `v*` tags, runs on `windows-latest` runner, uses PyInstaller to build EXE, creates GitHub Release with the artifact.

**Tech Stack:** GitHub Actions, PyInstaller, Python 3.12, `softprops/action-gh-release`

---

### Task 1: Create GitHub Actions Workflow Directory

**Files:**
- Create: `.github/workflows/release.yml`

**Acceptance Criteria:**
- [ ] Directory structure `.github/workflows/` exists
- [ ] Empty `release.yml` file created

**Reference:** Design doc section above

**Implementation Notes:**
- GitHub Actions expects workflows in `.github/workflows/`

---

### Task 2: Implement Release Workflow

**Files:**
- Modify: `.github/workflows/release.yml`

**Acceptance Criteria:**
- [ ] Triggers on `v*` tags only
- [ ] Runs on `windows-latest`
- [ ] Uses Python 3.12
- [ ] Builds EXE with PyInstaller
- [ ] Creates GitHub Release with EXE artifact
- [ ] Version extracted from tag (v1.0.0 → 1.0.0)

**Reference:** Design doc section above

**Implementation Notes:**
- Use `softprops/action-gh-release@v2` for release creation
- PyInstaller command: `pyinstaller -F -w -n llamacpp-panel --icon=llamacpp-panel.ico --add-data "llamacpp-panel.ico;." main.py`
- No test step required (user confirmed)

---

### Task 3: Verify and Commit

**Files:**
- Modify: `.github/workflows/release.yml`

**Acceptance Criteria:**
- [ ] YAML syntax valid
- [ ] File committed to git
- [ ] Ready for tag push test

**Implementation Notes:**
- No additional documentation updates needed for CI/CD
- User can test by pushing a tag after merge