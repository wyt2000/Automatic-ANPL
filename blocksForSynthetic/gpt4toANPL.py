import openai
import json
import pathlib
import time

background = '''You are a expert of ANPL programming language.
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

pre_prompt = "Please write an ANPL code, which has only one function should be named as `func_name`."

post_prompt = "Write out your reasoning first, and then describe your high-level solution and explain why it is correct. "

class GPT4toANPL:
    def __init__(self, background=background, pre_prompt=pre_prompt, post_prompt=post_prompt):
        self.background = background
        self.pre_prompt = pre_prompt
        self.post_prompt = post_prompt 

    def extract_code(self, response, func_name):
        func_head = f'def {func_name}'
        func_return = 'return'
        lines = response.split('\n')
        code = []
        ok = False
        for line in lines:
            if func_head in line:
                ok = True
            if ok:
                code.append(line)
            if func_return in line:
                ok = False
        return '\n'.join(code)


    def request(self, func_name, prompt, res_path):
        messages = [
            {"role": "system", "content": self.background},
            {"role": "user", "content": '\n'.join([
                    self.pre_prompt.replace("`func_name`", func_name),
                    prompt,
                    self.post_prompt.replace("`func_name`", func_name)
                ])
            }
        ]
        response = openai.ChatCompletion.create(model='gpt-4', messages=messages)
        status_code = response["choices"][0]["finish_reason"]
        assert status_code == "stop", f"The status code was {status_code}."
        response = response["choices"][0]["message"]["content"]
        with open(res_path, 'w') as f:
            f.write(response)
        return self.extract_code(response, func_name)

