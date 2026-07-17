from typing import Dict, Type, List, Optional, Any
from unilog.parsers.base import BaseParser

# Registry mapping format name -> Parser Class
_registry: Dict[str, Type[BaseParser]] = {}
_loaded = False

def _ensure_loaded():
    global _loaded
    if not _loaded:
        _loaded = True
        # Explicitly import all built-in parsers here to register them
        try:
            from unilog.parsers.json_log import JSONParser  # noqa: F401
            from unilog.parsers.custom import CustomParser  # noqa: F401
            from unilog.parsers.nginx import NginxParser  # noqa: F401
            from unilog.parsers.apache import ApacheParser  # noqa: F401
            from unilog.parsers.syslog import SyslogParser  # noqa: F401
            from unilog.parsers.django import DjangoParser  # noqa: F401
            from unilog.parsers.windows import WindowsParser  # noqa: F401
            # Other parsers will be imported here when added
        except ImportError:
            pass

def register_parser(cls: Type[BaseParser]) -> Type[BaseParser]:
    """Decorator to register a parser class with the registry."""
    if not issubclass(cls, BaseParser):
        raise TypeError(f"Parser class must inherit from BaseParser, got {cls.__name__}")
    
    name = getattr(cls, "name", None)
    if not name or name == "base":
        raise ValueError(f"Parser class must define a valid non-base name attribute, got {name}")
    
    _registry[name] = cls
    return cls

def get_parser(name: str) -> Optional[Type[BaseParser]]:
    """Retrieve a parser class by name."""
    _ensure_loaded()
    return _registry.get(name)

def list_formats() -> List[Dict[str, Any]]:
    """List all registered formats and their metadata."""
    _ensure_loaded()
    formats = []
    # Sort by priority desc, name asc
    sorted_parsers = sorted(
        _registry.values(),
        key=lambda cls: (-getattr(cls, "priority", 0), getattr(cls, "name", ""))
    )
    for cls in sorted_parsers:
        formats.append({
            "name": getattr(cls, "name", ""),
            "description": getattr(cls, "description", ""),
            "priority": getattr(cls, "priority", 0),
            "supported_extensions": getattr(cls, "supported_extensions", []),
            "class": cls
        })
    return formats
