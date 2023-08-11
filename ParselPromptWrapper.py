from PromptWrapper import AbstractPromptWrapper

_background = '''You are a expert of Parsel programming language.
Parsel is a natural language framework for writing programs for any target language using code language models. Parsel considers multiple implementations for each function, searching sets of implementations to find programs passing unit tests (more generally, program constraints). It can be used for many kinds of algorithmic tasks, e.g. code synthesis, robotic planning, and theorem proving. 
The syntax of Parsel is: 
{func}({arg}): {natural language description}.
{input} -> {output}
Attention: the natural language description of the function should be in one line.
Here is an example of Parsel code: 
\"\"\"
main(input): The input is a two-line str. Split the input by '\n' as two element list. Get the first element of the input, split it by space as n and k. Get the second element of the input, split it by space and convert it to int list as arr. Sorted arr in non-decreasing order. Get sum of the first k elements from arr as ans. Convert ans to str. Return ans.
'8 5\n1 1 1 1 1 1 1 1\n' -> '5'
\"\"\"
'''

_pre_prompt = "Please write a Parsel code, which has only one function should be named as `func_name`. The function should be in one line, and the second line should be a input-output example in format {input} -> {output}, when feed the function {input}. it should return {output}."

_post_prompt = "Please write Parsel code first, you should write out a single line \"\"\" both before and after your code, then write out your reasoning, and then describe your high-level solution and explain why it is correct. "


class ParselPromptWrapper(AbstractPromptWrapper):
    
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


