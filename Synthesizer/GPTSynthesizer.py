from .Synthesizer import AbstractSynthesizer

class GPTSynthesizer(AbstractSynthesizer):

    @property
    def name(self):
        return 'ChatGPT'

    def synthesize(self, code, save_path, *args):
        with open(save_path, "w") as f:
            f.write(code)
        return code

