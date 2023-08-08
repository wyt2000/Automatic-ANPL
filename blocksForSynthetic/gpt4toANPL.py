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

messages = []
system_message = {"role": "system", "content": background}
messages.append(system_message)

try:
    while True:
        input('Press Enter to read message from msg.txt:\n')
        msg = '' 
        with open('msg.txt', 'r') as f:
            lines = f.readlines() 
            msg = ''.join(lines)
        print(f'User:\n{msg}')
        user_message = {"role": "user", "content": msg}
        messages.append(user_message)
        response = openai.ChatCompletion.create(model='gpt-4', messages=messages)
        status_code = response["choices"][0]["finish_reason"]
        assert status_code == "stop", f"The status code was {status_code}."
        response = response["choices"][0]["message"]["content"]
        with open('response.txt', 'w') as f:
            f.write(response)
        print(f"ChatGPT:\n{response}")
        messages.append({"role": "assistant", "content": response})
finally:
    pathlib.Path("log").mkdir(parents=True, exist_ok=True)
    timestr = time.strftime("%m%d%H%M%S")
    with open(f"log/gpt-{timestr}.log", "w") as f:
        f.write(json.dumps(messages))
