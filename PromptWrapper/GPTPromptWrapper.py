from .PromptWrapper import AbstractPromptWrapper

#TODO: Read prompts from files.
_background = '''You are an expert of Python programming language.'''

_pre_prompt = "Please write a Python code, which has only one function should be named as `func_name`."

_post_prompt = "Please write Python code first, then write out your reasoning, and then describe your high-level solution and explain why it is correct."

class GPTPromptWrapper(AbstractPromptWrapper):
    
    @property
    def background(self):
        return _background

    @property
    def pre_prompt(self):
        return _pre_prompt

    @property
    def post_prompt(self):
        return _post_prompt

    def _transform_pre_prompt(self, args):
        func_name = args[0]
        return self.pre_prompt.replace("`func_name`", func_name)



