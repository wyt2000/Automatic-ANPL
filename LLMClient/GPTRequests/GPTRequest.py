from abc import abstractmethod
from ..LLMRequest import LLMRequest, LLMRequestManager

__all__ = ['GPTRequest', 'GPTRequestManager']

class GPTRequest(LLMRequest):

    async def __call__(self, *args):
        pass 


class GPTRequestManager(LLMRequestManager):

    def __init__(self):
        super().__init__(GPTRequest)
