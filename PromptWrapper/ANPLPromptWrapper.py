from .PromptWrapper import AbstractPromptWrapper

#TODO: Read prompts from files.
_background = '''You are an expert of ANPL programming language.
An ANPL program consists of a python-like sketch, and natural language holes.
A hole implements a function module with a natural language description, which will be fleshed out by LLMs during the compiling process. Each hole specified with a natural language description quoted by quotation marks `` or \"\"\". When called, holes should be organized by specifying its input-output variables, serving as the interconnections. To define a hole, users can either:
    1. define a hole as a sub-function with the function name, parameters, and descriptions, and then call the function with its function name and input-output variables, or
    2. just define and call it with descriptions and input-output variables inline.
A sketch is the control/data flow connecting different holes, specified with a programmatic language. Users constitute the sketch by assigning names to variables and using them as hole parameters in a data flow graph. Besides, users can write complex control flows with programmatic keywords (e.g., for, while, if) similar to that in Python to get more intricate ANPL programs.
Here is an example for ANPL:

def main(input):
    input = `Delete '\n' in the input`(input)
    n, m = `Split the input str by space and convert it to int as n and m`(input)
    n, m, ans = `Let ans as an empty str. If n > m, ans start with 'B', decrease n by 1, otherwise it start with 'G', decrease m by 1. Then alternately append 'B' and 'G' to then end of ans, meanwhile decreasing n and m by 1, until n = 0 or m = 0. Return n, m and ans.`(n, m)
    ans = `Append n 'B's and m 'G's to then end of ans.`(n, m, ans)
    ans += '\n'
    return ans
'''

_pre_prompt = "Please write an ANPL code, which has only one function should be named as `func_name`."

_post_prompt = "Please write ANPL code first, then write out your reasoning, and then describe your high-level solution and explain why it is correct. "

class ANPLPromptWrapper(AbstractPromptWrapper):
    
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



