# Engineering RFC: unilog v0.4 — Advanced Analytics Architecture

This document defines the finalized, frozen design for the **unilog v0.4 — Advanced Analytics** (Operational Intelligence Engine) subsystem.

---

## 1. Overall Analytics Architecture

The Operational Intelligence Engine implements a structured metrics compilation and rule execution pipeline:

```
[ Normalized Parsed Records ]  (JSON logs from parser engine)
              │
              ▼
    [ Metrics Engine ]         (Resolves and executes registered metrics analyzers)
              │
              ▼
    [ Metrics Bundle ]         (Consolidated metric models aggregate)
              │
              ▼
     [ Rule Engine ]           (Evaluates MetricsBundle against RuleSets)
              │
              ▼
    [ Analysis Result ]        (Canonical output response)
              │
              ▼
     [ API Endpoints ]         (Composed endpoints: /metrics, /insights, /analytics)
              │
              ▼
   [ Visual Dashboard ]        (React widgets and alert cards)
```

---

## 2. Dynamic Plugin Registry

Analyzers are registered using explicit metadata tags to verify dependency graphs and output formats at startup:

```python
# unilog/analytics/registry.py
_ANALYZER_REGISTRY = {}

def register_analyzer(name: str, version: str = "1.0", dependencies: list = None, produces: type = None):
    def decorator(cls):
        _ANALYZER_REGISTRY[name] = {
            "class": cls,
            "version": version,
            "dependencies": dependencies or [],
            "produces": produces
        }
        return cls
    return decorator
```

### Analyzer Interface
```python
# unilog/analytics/base.py
from pydantic import BaseModel, Field

class AnalyzerContext(BaseModel):
    window_minutes: int = Field(5, description="Size of analysis window")
    timezone: str = Field("UTC", description="Target evaluation timezone")
    bucket_seconds: int = Field(60, description="Granularity of sub-buckets")
    parser_metadata: dict = Field(default_factory=dict, description="Metadata from the parsed log format")

class BaseAnalyzer:
    """Abstract base class representing a metrics collector module."""
    
    def analyze(self, records: list[dict], context: AnalyzerContext) -> BaseModel:
        """Processes logs in context, returning a validated Metric model instance."""
        raise NotImplementedError("Analyzers must implement analyze.")
```

---

## 3. Data Schema Layer

Unified, structured data schemas serve as the stable communication contracts:

```python
from pydantic import BaseModel, Field

# --- Metric Models ---
class TrafficMetrics(BaseModel):
    timestamp: str
    total_requests: int
    requests_per_second: float
    volume_bytes: int

class ErrorMetrics(BaseModel):
    timestamp: str
    total_errors: int
    error_ratio: float
    errors_by_level: dict[str, int]

class LatencyMetrics(BaseModel):
    timestamp: str
    percentiles: dict[str, float]
    average_duration_ms: float

# --- Metrics Bundle ---
class MetricsBundle(BaseModel):
    traffic: TrafficMetrics | None = None
    error: ErrorMetrics | None = None
    latency: LatencyMetrics | None = None
    status: dict | None = None
    endpoint: dict | None = None

# --- Insight Event ---
class Insight(BaseModel):
    id: str
    category: str  # e.g., "security", "performance", "traffic", "reliability"
    severity: str  # e.g., "low", "medium", "high", "critical"
    confidence: float  # Evaluated as: Rule Confidence * Sample Size Factor
    timestamp: str
    description: str
    recommendation: str
    evidence: dict
    metadata: dict

# --- Canonical Analysis Result ---
class AnalysisResult(BaseModel):
    metrics: MetricsBundle
    insights: list[Insight]
    execution_time_ms: float
    analyzed_records: int
    ruleset_version: str
```

---

## 4. Rule Engine API Contract

The **Rule Engine** evaluates the compiled metrics using a configurable ruleset, yielding a structured list of actionable alert events:

```python
class RuleEngine:
    """Rule Engine evaluates MetricsBundles against RuleSets, producing Insights."""
    
    @staticmethod
    def evaluate(metrics: MetricsBundle, ruleset: dict) -> list[Insight]:
        """Runs metrics data evaluations against threshold limits."""
        insights = []
        # Evaluation steps...
        return insights
```

---

## 5. API Endpoints Schema

To keep frontend components composable and simple, backend routes are split:
- **`GET /api/v1/analytics/metrics`**: Serves `MetricsBundle` (for graph components).
- **`GET /api/v1/analytics/insights`**: Serves `list[Insight]` (for alert boxes).
- **`GET /api/v1/analytics/result`**: Serves the unified `AnalysisResult` (for combined panels).

---

## 6. Versioned Roadmap

- **Release 1: Core Subsystem Architecture** (Engine, Registry, MetricsBundle, AnalyzerContext).
- **Release 2: Core Metrics** (Traffic, Error, Status, Endpoint metric models).
- **Release 3: Performance Metrics** (Latency and IP distribution models).
- **Release 4: Decoupled Rule Engine** (Deterministic evaluation logic, RuleSets, Insight schema).
- **Release 5: React Dashboard Integration** (React selectors, transformers, custom charts hooks).
- **Release 6: Session Analytics** (Session reconstruction and user journeys).
- **Release 7: Security Analytics** (Brute force, scan signatures, traversals, and bot signatures).
