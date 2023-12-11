from abc import ABC, abstractmethod
from typing import Type

__all__ = ['LLMRequest', 'LLMRequestManager']

class LLMRequest(ABC):
    
    @abstractmethod
    async def __call__(self, *args):
        pass 

class LLMRequestManager(ABC):

    def __init__(self, requestType: Type[LLMRequest]):
        self._requestType   = requestType
        self._requests      = {}

    def add_request(self, *requests: Type[LLMRequest]):
        for req in requests:
            assert issubclass(req, self._requestType)
            self._requests[req.__name__] = req

    def __getattr__(self, name: str):
        if (attr := self._requests.get(name)) is not None:
            return attr
        return super().__getattribute__(name)

