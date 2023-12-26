from abc import ABC, abstractmethod
import logging

from Utils import CacheManager
from Configs import CONFIG

__all__ = ['LLMClient']

class LLMClient(ABC):
    
    def __init__(self,
                 cacheManager: CacheManager,
                 retry_times: int = CONFIG.LLM_retry_times,
                 retry_interval: int = CONFIG.LLM_retry_interval):

        self.logger             = logging.getLogger(f'{self.__class__.__name__}')
        self.cacheManager       = cacheManager 
        self.retry_times        = retry_times
        self.retry_interval     = retry_interval

    # TODO: Abstract for GPT and other LLMs
    @abstractmethod
    def request(self, *args):
        pass
