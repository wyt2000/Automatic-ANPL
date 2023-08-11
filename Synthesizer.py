from abc import ABC, abstractmethod 

class AbstractSynthesizer(ABC):
    '''
    Abstract base class of `Synthesizer`.
    '''

    @property
    @abstractmethod
    def name(self):
        '''
        Synthesizer name.
        '''


    @abstractmethod
    def synthesize(self, code, save_path, *args):
        '''
        :param code: Synthesizer's DSL code.
        :type code: str

        :param save_path: Path to save target program.
        :type save_path: str
        '''

