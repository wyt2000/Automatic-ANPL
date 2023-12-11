from ..LLMClient import LLMClient
from ..GPTRequests import GPTRequest, GPTRequestManager
from Utils import CacheManager
from Configs import CONFIG

__all__ = ['GPTClient']

class GPTClient(LLMClient):

    def __init__(self,
                 cacheManager: CacheManager,
                 requestManager: GPTRequestManager = None,
                 retry_times: int = CONFIG.GPT_retry_times):

        if requestManager is None:
            requestManager = GPTRequestManager()
            for request in GPTRequest.__subclasses__():
                requestManager.add_request(request)
        super().__init__(cacheManager, requestManager, retry_times)

        