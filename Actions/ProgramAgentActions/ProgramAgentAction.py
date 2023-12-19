from Actions.Action import Action
import logging

__all__ = ['ProgramAgentAction']

class ProgramAgentAction(Action):
    # Program action with config dict 
    def __init__(self, **config):
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.config = config

    def __repr__(self):
        return f'ProgramAgentAction({self.__class__.__name__}, {self.config})'