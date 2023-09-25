from abc import ABC, abstractmethod 

class AbstractSynthesizer(ABC):
    '''
    Abstract base class of `Synthesizer`.
    '''


    @abstractmethod
    def synthesize(self,
                   task_name: str,
                   code: str,
                   save_path_prefix: str,
                   *args):
        '''
        :param task_name: identify task for logger.
        :type code: str

        :param code: Synthesizer's DSL code.
        :type code: str

        :param save_path_prefix: Path to save target program.
        :type save_path: str
        '''
