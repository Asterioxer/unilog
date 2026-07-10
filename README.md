# unilog — Universal Log Parser

Parse any log file into a clean pandas DataFrame with zero configuration.

## Features

- **Zero Configuration**: Simply call `unilog.parse("any.log")`
- **Auto-Detection**: Dynamically detects formats based on heuristics, regex, and structured validation
- **Streaming Parser**: Stream lines instead of loading everything to memory using `unilog.stream("any.log")`
- **Pluggable Architecture**: Easily register custom formats and statistics analyzers
- **Anomaly Detection**: Find traffic volume spikes, error rate spikes, and new IP access anomalies
- **Rich CLI**: Pretty output format choices including json, csv, and table

## Supported Formats

| Format | Auto-detected | Fields extracted |
| :--- | :--- | :--- |
| Nginx access (combined) | ✅ | ip, timestamp, method, path, status, size, ua |
| Apache access (combined) | ✅ | ip, timestamp, method, path, status, size, ua |
| Syslog RFC 3164 | ✅ | timestamp, hostname, process, pid, message |
| Syslog RFC 5424 | ✅ | timestamp, hostname, app, msgid, message |
| JSON logs | ✅ | all keys as columns |
| Django/Python logging | ✅ | timestamp, level, logger, message |
| Windows Event Log | ✅ | timestamp, level, source, event_id, message |
| Custom (user-defined) | manual | user-specified named groups |

## Installation

```bash
pip install unilog
```

## Quick Start

```python
import unilog

# Auto-detect format and parse
df = unilog.parse("access.log")
```
