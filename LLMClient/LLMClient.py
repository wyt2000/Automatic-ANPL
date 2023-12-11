from abc import ABC, abstractmethod
import logging

from Utils import CacheManager
from .LLMRequest import LLMRequestManager

__all__ = ['LLMClient']

class LLMClient(ABC):
    
    def __init__(self,
                 cacheManager: CacheManager,
                 requestManager: LLMRequestManager,
                 retry_times: int):

        self.logger             = logging.getLogger(f'{self.__class__.__name__}')
        self.cacheManager       = cacheManager 
        self.requestManager     = requestManager
        self.retry_times        = retry_times

    @property
    def request(self):
        return self.requestManager
