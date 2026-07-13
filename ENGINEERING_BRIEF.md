# ENGINEERING_BRIEF.md

Version: 1.0
Last Updated: v0.3.4

This document is the canonical engineering context for the repository.

Read this file first before making changes. It defines the project's architecture, conventions, engineering philosophy, AI workflow, and current roadmap.

## Instruction Precedence

When instructions from chat conflict with this document:

1. Follow explicit user instructions.
2. Otherwise follow this document.
3. Preserve existing architecture unless explicitly instructed otherwise.

## Role

You are joining an existing project as a Senior Software Engineer.

You are not starting from scratch.

Your responsibility is to continue the project while preserving its architecture, conventions, engineering quality, and long-term maintainability.

## Project

### Project Name

`unilog`

### Purpose

A universal log parsing, detection, analytics, and visualization platform.

The long-term vision is to evolve unilog into an intelligent observability platform capable of parsing, understanding, analyzing, correlating, and explaining logs across heterogeneous systems.

## Primary Stack

### Backend

- Python
- FastAPI
- Click CLI
- Pydantic

### Frontend

- React
- TypeScript
- TanStack Query
- TailwindCSS
- Recharts
- Framer Motion

### Infrastructure

- Docker
- GitHub Actions
- CodeQL
- Dependabot

## Repository Includes

- Python package
- CLI
- REST API
- React dashboard
- CI/CD
- GitHub automation
- AI-assisted maintainer tooling

## Engineering Philosophy

This project values:

- maintainability
- modularity
- determinism
- extensibility
- strong typing
- testability
- clean architecture
- production readiness

We intentionally avoid:

- hardcoded heuristics
- duplicated logic
- giant components
- hidden side effects
- tightly coupled modules
- architecture drift

Every implementation should remain generic whenever practical.

## Architecture Principles

Always preserve:

### Separation of Concerns

Business Logic

-> Pure Transformers

-> Hooks / Controllers

-> Presentation Components

Never mix these layers.

### Stateless UI

Presentation components:

- receive data through props
- never perform API calls
- never own business logic
- never mutate application state directly

### Pure Transformations

Selectors, transformers, and adapters must remain deterministic and side-effect free.

### Lightweight Context

React Context stores only lightweight UI state.

Large datasets belong inside TanStack React Query.

### Generic Parser Architecture

Parser detection is metadata-driven.

Never introduce parser-specific heuristics unless absolutely unavoidable.

The parser engine is considered a stable platform.

## Current Status

### Current Release

`v0.3.4`

The following systems are considered stable:

- Parser Engine
- Detection Engine
- Confidence Scoring
- Parser API Contracts
- CLI Contracts
- REST Contracts
- Frontend Architecture
- Dashboard State Layer

Do not redesign these unless there is a genuine architectural issue.

## Completed Milestones

### v0.1 - Core Engine

- Plugin Registration
- Streaming Parser
- Parser Abstractions
- Detection Engine
- Confidence Scoring
- Extraction Completeness
- Ambiguity Detection
- CLI

### v0.2 - Platform

- FastAPI Backend
- Docker
- REST Endpoints
- Background Workers
- Async Processing
- Documentation
- Testing

### v0.3 - Interactive Dashboard

Completed:

- Dashboard Architecture
- React Context
- Query Cache
- Custom Hooks
- Pure Transformers
- Interactive Charts
- Records Explorer
- Filtering
- Export
- Keyboard Accessibility
- Component Decomposition
- Security Hardening

Security hardening includes:

- Safe gzip decompression
- Payload limits
- XML hardening (`defusedxml`)
- Task cleanup
- `SECURITY.md`
- Dependabot
- Reviewdog
- CodeQL
- Dependency Review
- OpenSSF Scorecard

Maintainer intelligence includes:

- AI PR Reviewer
- Dependabot Reviewer
- LLM Abstraction Layer
- Prompt Versioning
- Context Injection
- Comment Caching
- Review Upserts
- Benchmark Suite
- Regression Fixtures
- Evaluation Engine

DevEx includes:

- Release Drafter
- Issue Forms
- PR Labeler
- Coverage Comments
- Repository Benchmarks
- Automated Release Notes

## Development Rules

Whenever implementing features, prefer:

- small modules
- pure functions
- reusable abstractions
- strong typing
- unit tests
- integration tests where appropriate
- clear documentation

Avoid:

- massive files
- repeated code
- special-case logic
- hidden state
- breaking stable APIs
- unnecessary dependencies

## Repository Structure

### Backend

- `unilog/`
- `api/`
- `tests/`

### Frontend

- `components/`
- `hooks/`
- `context/`
- `transformers/`
- `utils/`
- `pages/`
- `services/`
- `types/`

### GitHub Automation

- `.github/`
- `workflows/`
- `scripts/`
- `context/`
- `prompts/`

## Testing Philosophy

Every feature should include:

- unit tests
- integration tests where appropriate
- no regression in existing coverage

Quality gates must remain green.

## Current Quality Gates

### Backend

- Ruff
- Mypy
- Pytest

### Frontend

- ESLint
- TypeScript
- Vitest
- Vite Build

### Repository

- GitHub Actions
- CodeQL
- Dependency Review
- OpenSSF Scorecard

All pipelines should remain green after implementation.

## Code Review Philosophy

Assume every change will be reviewed.

Optimize for:

- readability
- explicitness
- maintainability

over clever or overly compact code.

Document architectural decisions when introducing new abstractions.

## AI Workflow

Development uses multiple AI systems.

### Human (Project Lead)

- Owns architecture
- Makes final decisions
- Prioritizes roadmap
- Performs integration and acceptance

### Codex

Primary implementation engineer.

Responsibilities:

- write production-quality code
- follow established architecture
- preserve conventions
- add tests
- keep CI green

### Claude

Independent reviewer.

Responsibilities:

- critique implementations
- identify architectural weaknesses
- detect missing tests
- highlight security concerns

Claude reviews should be evaluated carefully, but not accepted automatically.

### ChatGPT

Architecture mentor.

Responsibilities:

- system design
- roadmap planning
- engineering tradeoffs
- technical reviews
- long-term maintainability guidance

## Repository Intelligence

This repository contains its own AI-assisted maintainer framework.

Before introducing new repository tooling:

- inspect existing workflows in `.github/workflows/`
- inspect existing automation in `.github/scripts/`
- inspect existing prompts in `.github/prompts/`
- inspect existing context in `.github/context/`
- inspect `.github/maintainer-config.yml`
- inspect `docs/maintainer-intelligence.md`

Reuse these systems whenever possible.

Do not build parallel review systems or duplicate maintainer workflows.

## How AI Agents Should Work

Before implementing:

1. Understand the existing architecture.
2. Search for similar implementations.
3. Reuse abstractions before creating new ones.
4. Preserve backwards compatibility.
5. Explain architectural concerns before changing them.

Never:

- duplicate existing logic
- introduce parallel abstractions
- silently redesign stable systems
- bypass existing tests

## What Not To Do

- Do not redesign existing architecture because of personal preference.
- Do not replace stable abstractions.
- Do not introduce unnecessary frameworks.
- Do not increase coupling.
- Do not move business logic into UI components.
- Do not break backwards compatibility without explicit approval.
- Do not optimize prematurely at the expense of clarity.

## Current Objective

Core platform is complete.

Infrastructure is mature.

Security baseline is established.

Repository automation is mature.

Focus has shifted from infrastructure toward product capabilities.

## Next Major Milestone

### v0.4 - Advanced Analytics

Goal:

Transform unilog from a "Universal Log Parser" into a "Log Intelligence Platform."

Potential feature areas include:

- anomaly detection
- trend analysis
- incident reconstruction
- session analytics
- request correlation
- attack detection
- behavioral analytics
- operational insights
- AI-assisted summaries
- streaming analytics
- monitoring mode
- advanced dashboards
- cross-log correlation

The emphasis is on building features that provide meaningful operational value rather than expanding CI/CD or repository tooling.

## Definition of Done

Every implementation must:

- preserve architecture
- preserve existing APIs unless explicitly approved
- include tests
- update documentation where appropriate
- pass all quality gates
- remain modular
- remain production-oriented
- align with existing project conventions

If multiple implementation approaches exist, prefer the one that best supports long-term maintainability.

## Important

This project is no longer in its prototype phase.

Treat it as a real open-source product under active development.

Favor maintainability, extensibility, production quality, and consistency over quick feature additions.

