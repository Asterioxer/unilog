# Security Policy

We take the security of `unilog` seriously. If you believe you have found a security vulnerability, please report it to us using the instructions below.

## Supported Versions

Only the latest release (and active release candidates) are actively supported with security updates:

| Version | Supported |
| :--- | :--- |
| v0.3.x | Yes (latest candidate v0.3.1) |
| < v0.3.0 | No |

## Reporting a Vulnerability

Please do not report security vulnerabilities via public GitHub issues. Instead, report them privately:

* **Contact**: Send an email to `sohamaxpauli@gmail.com` with details of the threat.
* **Details**: Please include:
  - Component or endpoint affected.
  - A clear step-by-step description of the vulnerability.
  - A Proof-of-Concept (PoC) or script to reproduce the exploit.
  - The potential impact (e.g., DoS, resource exhaustion).

## Security Boundaries & Guarantees

`unilog` guarantees operational safety when deployed inside Docker or as a standalone FastAPI REST service under the following boundaries:

* **Compressed Archives Protection**: Synchronous and asynchronous upload decompression is restricted chunk-by-chunk up to `UNILOG_MAX_DECOMPRESSED_SIZE` to prevent decompression/zip bomb memory spikes.
* **Safe XML Parsing**: Windows XML Event logs are parsed using `defusedxml` to block DTD entity expansions and billion laughs attacks.
* **Bounded Queue Storage**: Background tasks are stored in memory up to `UNILOG_MAX_TASKS` with a TTL limit of `UNILOG_TASK_TTL_SECONDS` to prevent infinite memory leaks.
* **JSON Size Caps**: JSON endpoint string variables (`log_text`) are restricted via Pydantic model length validations.

## Operational Security Controls

`unilog` implements operational security hardening configurations for production deployments:

* **Proxy-Aware Rate Limiting**: Configure `UNILOG_TRUST_PROXY=true` and `UNILOG_TRUSTED_PROXIES=127.0.0.1,10.0.0.1` (comma-separated IP whitelist) to resolve genuine client IP addresses through trusted reverse proxies.
* **Configurable CORS & CSP**: Dynamic CORS origins are configurable via `UNILOG_CORS_ORIGINS`. Response Content-Security-Policy headers can be configured using the `UNILOG_CSP` environment variable (defaults to `default-src 'self'; frame-ancestors 'none';`).
* **Safe Error Handling**: Internal tracebacks, raw exceptions, and file system paths are suppressed on client responses and recorded to structured server logs containing `request_id` and `client_ip` contexts.
* **Dependency Auditing**: Supply chain vulnerability scanning is integrated using `pip-audit` checks in CI.

## Out-of-Scope Issues

The following concerns are out of scope for the core `unilog` library and should be addressed by your deployment orchestration layer:

* HTTPS / TLS termination (this should be handled by reverse proxies like Nginx, Traefik, or Caddy).
* OAuth/OIDC, JWT, or Role-Based Access Controls (RBAC).
* Persistent long-term storage of tasks (tasks database is ephemeral).

## Disclosure Timeline

We follow coordinated vulnerability disclosure. Once a vulnerability report is received:

1. We will acknowledge receipt of the report within 48 hours.
2. We will investigate the issue and coordinate a patch within 15 days.
3. We will release a security update patch and publish a security advisory.
