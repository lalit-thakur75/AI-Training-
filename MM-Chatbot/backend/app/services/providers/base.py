from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseProvider(ABC):
    name: str = "base"
    supports_vision: bool = False

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if required credentials are set."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns configured model identifier."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        context_str: Optional[str] = None
    ) -> str:
        """Generates text completion from chat messages."""
        pass

    @abstractmethod
    async def generate_vision(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        """Answers questions about image contents."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Lightweight diagnostic connectivity check without expensive generation."""
        pass
