import openai
import json
import pathlib
import time
import re

background = '''You are a expert of Parsel programming language.
Parsel is a natural language framework for writing programs for any target language using code language models. Parsel considers multiple implementations for each function, searching sets of implementations to find programs passing unit tests (more generally, program constraints). It can be used for many kinds of algorithmic tasks, e.g. code synthesis, robotic planning, and theorem proving. The following are some prombles and the Parsel codes to solve them.
Here is an example calculating the probability of landing on the same character in a random shift of an input string, based on the following:
Problem:
     Vasya and Kolya play a game with a string, using the following rules. Initially, Kolya creates a string s, consisting of small English letters, and uniformly at random chooses an integer k from a segment [0, len(s) - 1]. He tells Vasya this string s, and then shifts it k letters to the left, i.e. creates a new string t = s_k + 1s_k + 2... s_ns_1s_2... s_k. Vasya does not know the integer k nor the string t, but he wants to guess the integer k. To do this, he asks Kolya to tell him the first letter of the new string, and then, after he sees it, open one more letter on some position, which Vasya can choose.
    Vasya understands, that he can’t guarantee that he will win, but he wants to know the probability of winning, if he plays optimally. He wants you to compute this probability.
    Note that Vasya wants to know the value of k uniquely, it means, that if there are at least two cyclic shifts of s that fit the information Vasya knowns, Vasya loses. Of course, at any moment of the game Vasya wants to maximize the probability of his win.
\"\"\"

'''

pre_prompt = "Please write an ANPL code, which has only one function should be named as `func_name`."

post_prompt = "Write out your reasoning first, and then describe your high-level solution and explain why it is correct. "

class GPT4toANPL:
    def __init__(self, background=background, pre_prompt=pre_prompt, post_prompt=post_prompt):
        self.background = background
        self.pre_prompt = pre_prompt
        self.post_prompt = post_prompt 

    def extract_code(self, response):
        func_head = re.compile("def .+\(.+\)\:")
        func_return = 'return'
        lines = response.split('\n')
        code = []
        ok = False
        for line in lines:
            if func_head.match(line):
                ok = True
            if ok:
                code.append(line)
            if ok and func_return in line:
                break
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
        return self.extract_code(response)

