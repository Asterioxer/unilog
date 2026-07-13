"""Registration and dependency resolution for analytics analyzers."""

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Type

from pydantic import BaseModel

from unilog.analytics.base import BaseAnalyzer


@dataclass(frozen=True)
class AnalyzerRegistration:
    """Metadata required to execute an analyzer predictably."""

    name: str
    analyzer_class: Type[BaseAnalyzer]
    version: str
    dependencies: Tuple[str, ...]
    produces: Optional[Type[BaseModel]]


_ANALYZER_REGISTRY: Dict[str, AnalyzerRegistration] = {}


_DISCOVERED = False


def _ensure_discovered() -> None:
    global _DISCOVERED
    if not _DISCOVERED:
        _DISCOVERED = True
        discover_analyzers()


def discover_analyzers() -> None:
    """Dynamically discover and import all custom analyzer modules."""
    import unilog.analytics.modules as modules
    for _, name, _ in pkgutil.iter_modules(modules.__path__):
        importlib.import_module(f"unilog.analytics.modules.{name}")


def register_analyzer(
    name: str,
    version: str = "1.0",
    dependencies: Optional[Sequence[str]] = None,
    produces: Optional[Type[BaseModel]] = None,
) -> Callable[[Type[BaseAnalyzer]], Type[BaseAnalyzer]]:
    """Register an analyzer class with its explicit execution metadata."""
    _validate_metadata(name, version, dependencies, produces)
    dependency_names = tuple(dependencies or ())

    def decorator(analyzer_class: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
        if not issubclass(analyzer_class, BaseAnalyzer):
            raise TypeError(
                "Analyzer class must inherit from BaseAnalyzer, "
                f"got {analyzer_class.__name__}."
            )
        if name in _ANALYZER_REGISTRY:
            raise ValueError(f"Analyzer '{name}' is already registered.")

        _ANALYZER_REGISTRY[name] = AnalyzerRegistration(
            name=name,
            analyzer_class=analyzer_class,
            version=version,
            dependencies=dependency_names,
            produces=produces,
        )
        return analyzer_class

    return decorator


def get_analyzer(name: str) -> Optional[AnalyzerRegistration]:
    """Return the registered analyzer metadata for ``name`` when available."""
    _ensure_discovered()
    return _ANALYZER_REGISTRY.get(name)


def list_analyzers() -> List[AnalyzerRegistration]:
    """List analyzers in stable name order for diagnostics and startup checks."""
    _ensure_discovered()
    return sorted(_ANALYZER_REGISTRY.values(), key=lambda registration: registration.name)


def validate_analyzer_registry() -> None:
    """Validate analyzer metadata and the complete dependency graph."""
    _ensure_discovered()
    for registration in _ANALYZER_REGISTRY.values():
        if registration.produces is None:
            raise ValueError(
                f"Analyzer '{registration.name}' must declare its produced metric model."
            )
    resolve_analyzers()


def resolve_analyzers(names: Optional[Iterable[str]] = None) -> List[AnalyzerRegistration]:
    """Resolve registered analyzers in dependency-first execution order."""
    _ensure_discovered()
    requested_names = tuple(names) if names is not None else tuple(_ANALYZER_REGISTRY)
    resolved: List[AnalyzerRegistration] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            raise ValueError(f"Circular analyzer dependency detected at '{name}'.")

        registration = _ANALYZER_REGISTRY.get(name)
        if registration is None:
            raise ValueError(f"Analyzer dependency '{name}' is not registered.")

        visiting.add(name)
        for dependency in registration.dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        resolved.append(registration)

    for requested_name in requested_names:
        visit(requested_name)

    return resolved


def _validate_metadata(
    name: str,
    version: str,
    dependencies: Optional[Sequence[str]],
    produces: Optional[Type[BaseModel]],
) -> None:
    if not name or not name.strip():
        raise ValueError("Analyzer name must be a non-empty string.")
    if not version or not version.strip():
        raise ValueError("Analyzer version must be a non-empty string.")
    if dependencies and any(not dependency or not dependency.strip() for dependency in dependencies):
        raise ValueError("Analyzer dependencies must contain non-empty names.")
    if produces is not None and not issubclass(produces, BaseModel):
        raise TypeError("Analyzer produces must be a Pydantic BaseModel subclass.")