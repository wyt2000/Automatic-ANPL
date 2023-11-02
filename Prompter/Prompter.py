background = """You are an expert of Python programming language. """

function_completion_prompt = """{prefix}
Here is a python program: 
-----Program-----
```
{code}
```

Here is an unimplemented function of the program:
-----Function-----
```
{hole}
```

-----Task-----
Complete the function. Add docstring to describe the new function you generated if it doesn't have one.
Your output should be in the following format:

```
python code
```

"""


pretest_prompt = """-----Question-----
{question}
-----Task-----
Give an assert test for this question in the following format. Each assert statement should be on one line.

-----Test-----
```
assert 
```

You should only output the assert test. Omit explanations or any additional text.
"""

solution_debug_prompt = """-----Question-----
{question}

-----Solution-----
{solution}

-----Test-----
{counterexample}

-----Task-----
The solution can't pass the test mentioned above.
Give the fixed high-level solution which can pass the assert test.
You should only output fixed high-level solution without any pseudocode or code.
"""

function_debug_prompt = """-----Question-----
{question}

-----Solution-----
{solution}

Here is an program implementation of the solution.
-----Program-----
{program}

Here is a function of the program with input-output traces. 
-----Function-----
{function_with_traces}

-----Task-----
If there are some mistakes or exceptions in the function, return the fixed function. You can define helper functions before it to decompose it into sub-functions.
Your output should be in the following format:
```
def {func_name}(...):
    '''
    The description of the function.
    '''
```
You should only output the function code! Omit explanations or any additional text!
"""

counterexample_prompt = """-----Question-----
{question}

-----Program-----
{program}

-----Task-----
Give an input example of the question and its corresponding correct output, which meet the input-output requirements of the question, but the program will return an incorrect output for this input. 
Your output should be in the following format:

-----Input-----
```
Input
```

-----Output-----
```
Output
```

"""

solution_prompt = """-----Question-----
{question}

-----Task-----
Propose a clever and efficient high-level solution for this problem. Consider all edge cases and failure modes.

Some common strategies include:
    Constructive algorithms, Binary search, Depth-first search (DFS) and similar algorithms, Dynamic programming, Bitmasks, Brute force, Greedy algorithms, Graphs, Two pointers, Trees, Geometry, Graph matchings, Hashing, Probabilities, Data structures, Sortings, Games, Number theory, Combinatorics, Divide and conquer, Disjoint set union (DSU), Expression parsing

Let's think step by step to come up with a clever algorithm.
You should only output high-level solution without any pseudocode or code.
"""

translation_prompt = """-----Question-----
{question}

-----Solution-----
{solution}

-----Task-----
Translate the solution for the problem into python code in the following format:

-----Program-----
```
python code
```

You should define some helper functions before function {entry_point} to decompose it. Each function should be described by docstring.
You should only output the python code! Omit explanations or any additional text!
"""

