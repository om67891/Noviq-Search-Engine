from abc import ABC, abstractmethod
from typing import Dict, Any, Type, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generates a raw string response."""
        pass
        
    @abstractmethod
    def generate_structured(self, prompt: str, output_schema: Type[T], system_prompt: Optional[str] = None) -> T:
        """Generates a response adhering to a Pydantic schema."""
        pass
