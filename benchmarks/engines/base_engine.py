class ReviewEngine:
    """Abstract base class for Review Engines in the Maintainer Intelligence framework."""
    
    def review(self, diff_content: str, metadata: dict) -> dict:
        """Executes a pull request review based on diff and metadata, returning a parsed JSON review dict."""
        raise NotImplementedError("Subclasses must implement review.")
