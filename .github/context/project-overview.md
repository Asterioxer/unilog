Context-Version: 1

# Project Overview

`unilog` is an extensible log analytics platform designed to solve the problem of parsing, auto-detecting, analyzing, and exploring diverse log file formats (e.g. Nginx, Apache, Syslog, Python, Windows Event logs, JSON) without user configuration.

## Key Features

1. **Parser Engine**: Support for multiple formats with heuristic confidence scoring.
2. **Streaming & CLI**: A command-line client supporting streaming lines and output formatting.
3. **REST API**: Built on FastAPI, supporting synchronous uploads, background queues, and rate-limiting.
4. **Interactive Dashboard**: A React SPA with Vitest, ESLint, React Query Cache, charts, and a highly responsive Records Explorer table.
5. **Operational Security**: Bound constraints for memory, safe decompression, and defused XML processing.
