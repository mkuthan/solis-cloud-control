# AGENTS.md

## Project Overview

This is the Solis Cloud Control API integration for Home Assistant.

## Setup Commands

- Install dependencies: `uv sync`
- Run tests: `uv run pytest`
- Run linter: `uv run ruff check`
- Run type checker: `uv run ty check`
- Format code: `uv run ruff format`

## General rules

- Always ask if you are unsure what to do or if the potential impact of a change is large
- Comments: Use sparingly, explain WHY not WHAT
- Mirror patterns from existing integration modules under `custom_components/solis_cloud_control` and tests under `tests`.
- Prioritize maintainability, testability, and performance while matching existing simplicity. Follow logging, typing, and retry patterns already used.

## Architecture & Module Boundaries

- `api/`: Low-level Solis Cloud API client & error types.
- `inverters/` & `domain/`: Domain model abstractions (value objects, bitfields, configuration holders) for inverter capabilities.
- `coordinator.py`: Data retrieval + control orchestration with retry & verification loops.
- `entity.py`: Base entity tying coordinator data to Home Assistant entities (availability logic).
- Platform files (`number.py`, `sensor.py`, `switch.py`, `select.py`, `text.py`): Entity classes mapping domain model CIDs to HA platform features with consistent naming and logging.
- `config_flow.py`: User onboarding (two-step: credentials -> inverter selection) with error mapping.
- `diagnostics.py`: Redacted diagnostic dump (serial number masked) using `asdict` from dataclasses.
- `__init__.py`: Integration setup, device registration, migration logic, coordinator instantiation.
