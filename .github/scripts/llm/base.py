class BaseLLMClient:
    """Abstract Base Class for LLM API Clients to ensure vendor-independence."""
    
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Sends a prompt to the LLM model and returns the generated text response."""
        raise NotImplementedError("Subclasses must implement generate_text.")
