# 📁 unilog Sample Log Datasets (`examples/`)

This directory contains real-world and synthetic sample log datasets for testing, benchmarking, and developing custom parsers/rules in `unilog`.

## 📜 Datasets Included

| File | Description | Target Parser |
| :--- | :--- | :--- |
| [`nginx_access.log`](file:///c:/Users/soham/Desktop/unilog/examples/nginx_access.log) | Nginx Combined Access Log payload | `nginx` |
| [`apache_access.log`](file:///c:/Users/soham/Desktop/unilog/examples/apache_access.log) | Apache Common Access Log format | `apache` |
| [`syslog_system.log`](file:///c:/Users/soham/Desktop/unilog/examples/syslog_system.log) | Linux `syslog` / `sshd` system events | `syslog` |
| [`security_attack.log`](file:///c:/Users/soham/Desktop/unilog/examples/security_attack.log) | SQLi, XSS, Path Traversal & Scanner attack logs | `nginx` / `apache` |

## 🧪 How to Test with CLI

```bash
# Parse Nginx access log
unilog parse examples/nginx_access.log --format nginx

# Auto-detect format & compute metrics
unilog detect examples/security_attack.log
```
