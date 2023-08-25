from abc import ABC, abstractmethod

class AbstractPrompter(ABC):
    '''
    Abstract base class of `PromptConfig`.
    '''

    @abstractmethod
    def get_background(self, **kwargs):
        '''
        Backgroud information of the task and the synthesizer.
        '''
        pass

    @abstractmethod
    def get_solution_prompt(self, **kwargs):
        '''
        How to generate high-level solutions.
        '''
        pass

    @abstractmethod
    def get_translation_prompt(self, **kwargs):
        '''
        How to translate high-level solutions to synthesizer's DSL.
        '''

    @abstractmethod
    def get_code_description(self, **kwargs):
        '''
        Other information about output codes.
        '''
        pass

