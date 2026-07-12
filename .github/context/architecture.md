Context-Version: 1

# Architecture Overview

`unilog` uses a strict layered design to decouple formats, operations, and presentations.

## Components & Modules

### 1. Parser Core (`unilog/`)
- `unilog/parsers/`: Core formatting engines (`BaseParser`, `RegexParser`, `StructuredRegexParser`).
- `unilog/detector.py`: Heuristics and confidence scoring logic.
- `unilog/registry.py`: Holds references to registered parsers.
- `unilog/cli.py`: Command line entry point.

### 2. REST API Engine (`api/`)
- `api/app.py`: FastAPI server configuration, slowapi rate-limits, and configuration validations.
- `api/routers/log.py`: Endpoint handlers (/parse, /detect, /stats, /upload, /tasks).
- `api/services/background_tasks.py`: In-memory tasks database with eviction controls.
- `api/utils/decompression.py`: Safe, chunk-bounded gzip decompressor.

### 3. Frontend Dashboard (`frontend/`)
- Single Page Application built on React, TypeScript, and Vite.
- React Query handles caching and remote parsing state management.
- Reusable logs table composed of specialized components under `components/table/` and state hooks in `hooks/useTableState.ts`.
