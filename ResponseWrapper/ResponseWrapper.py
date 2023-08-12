from abc import ABC, abstractmethod 

class AbstractResponseWrapper(ABC):
    '''
    Abstract base class of `ResponseWrapper`.
    Extract synthesizer's DSL from ChatGPT response.
    '''

    @abstractmethod
    def wrap(self, response, *args):
        '''
        :param response: ChatGPT response, contains DSL and maybe some explanations.
        :type response: str

        :return: The input DSL of synthesizer.
        :rtype: str
        '''

