# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nsynca is a Python toolkit that syncs and updates Notion databases via the official REST API. It automates project management tasks: tracking deployment metrics, task completion, subscription status, and auto-creating billing charge records.

## Commands

```bash
# Run linting
make lint

# Auto-fix and format
make fix

# Run GUI (local, no Docker)
make gui

# Run CLI (all updaters)
uv run main.py

# Run specific updaters
uv run main.py --updaters deployment task
uv run main.py --updaters service charge --log-level DEBUG

# Docker
make build       # Build image
make dev         # Run with hot reload
make run         # Run all updaters
make deploy / make task / make service / make charge  # Run specific updater

# Build Windows exe
make build-exe   # Generate PyInstaller spec
make compile-exe # Compile to .exe
```

There are no automated tests in this project.

## Architecture

### Entry Points
- `main.py` — CLI: parses `--updaters`, `--log-level`, `--parallel` args, then calls `PageUpdaterOrchestrator.run()`
- `gui.py` — GUI: launches `NotionUpdaterGUI` (customtkinter, dark theme)

### Core Data Flow
```
NotionWrapper  →  Updater  →  PageUpdaterOrchestrator  →  results
(API client)      (logic)      (coordinates all updaters)
```

### Updater Hierarchy
- `PageUpdaterBase` — abstract base: `get_page_info()`, `apply_updates()`, abstract `process_page()` / `run()`
- `ProjectUpdaterBase(PageUpdaterBase)` — adds project-specific naming aliases
- `DeploymentUpdater`, `TaskUpdater` extend `ProjectUpdaterBase`
- `ServiceUpdater`, `ChargeUpdater` extend `PageUpdaterBase` directly

### Data Models (`src/databases/`)
Each database module defines a domain object and a collection class. Models parse raw Notion API responses into typed Python objects with computed properties. Collections group objects and provide utility methods (grouping, filtering).

### Service vs Charge distinction
Services (`src/databases/services.py`) represents both "Service Profile" entries (subscriptions) and "Charge" entries (individual billing records) — distinguished by the `entry_type` property. `ServiceUpdater` handles status/next-due-date computation; `ChargeUpdater` creates missing monthly/yearly charge records by comparing expected vs. existing charge dates.

### GUI Architecture (`gui/`)
`NotionUpdaterGUI` monkey-patches `NotionWrapper.update_page` and `create_page` at startup to intercept all API calls and feed them to a queue for real-time progress display. Updates run in a background thread (`UpdateRunner`), results are logged as JSON files in `logs/`, and `LogsViewer` displays historical logs with filtering.

## Key Constraints

- **Python 3.11 only** — `pyproject.toml` pins `requires-python = ">=3.11, <3.12"`
- Uses `uv` for dependency management (not pip/poetry)
- Conventional commits enforced by pre-commit (commitizen); subject line ≤50 chars
- Commit secrets scanned by gitleaks on pre-push

## Environment Variables

Required in `.env` (see `.env.example`):
- `NOTION_API_KEY` — Notion integration token
- `DEPLOYMENTS_DB_ID`, `TASKS_DB_ID`, `SERVICES_DB_ID` — Notion database UUIDs
- `GITHUB_USERNAME`, `GITHUB_TOKEN` — only needed for Docker registry push
