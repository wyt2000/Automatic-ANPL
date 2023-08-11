from abc import ABC, abstractmethod 

class AbstractPromptWrapper(ABC):
    '''
    Abstract base class of `PromptWrapper`.
    Transform program descriptions to the prompts for ChatGPT according to specific promgram synthesizer.
    '''

    @property
    @abstractmethod
    def backgroud(self):
        '''
        The role of chatGPT and syntax rules or examples of the synthesizer's DSL.
        eg: You are an expert of {synthesizer's DSL} programming language. The following are some examples for you...
        '''

    @property
    @abstractmethod
    def pre_prompt(self):
        '''
        Something before function descriptions.
        eg: Please write a {synthesizer's DSL} code, which has only one function named {func_name}.
        '''

    @property
    @abstractmethod
    def post_prompt(self):
        '''
        Something after function descriptions.
        eg: You should write out a single line \"\"\" both before and after your code, then explain why the code is correct.
        '''

    def _transform_raw_prompt(self, raw_prompt, args):
        '''
        Modify prompt if need.
        eg: convert {func_name} in str to real func_name.
        '''
        return raw_prompt

    def _transform_pre_prompt(self, args):
        return self.pre_prompt

    def _transform_post_prompt(self, args):
        return self.post_prompt

    def warp(self, raw_prompt, *args):
        '''
        Convert function descriptions to ChatGPT prompts.
        :param raw_prompt
        :type raw_prompt: str
        '''
        return '\n'.join([
            self._transform_pre_prompt(args),
            self._transfrom_raw(raw_prompt, args),
            self._transform_post_prompt(args)
        ])



