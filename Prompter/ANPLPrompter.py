from .Prompter import AbstractPrompter

class ANPLPrompter(AbstractPrompter):
    
    def get_background(self, **kwargs):
        return _background.format(**kwargs)

    def get_pretest_prompt(self, **kwargs):
        return _pretest_prompt.format(**kwargs)

    def get_solution_prompt(self, **kwargs):
        return _solution_prompt.format(**kwargs)

    def get_translation_prompt(self, **kwargs):
        return _translation_prompt.format(**kwargs) + self.get_code_description(**kwargs)

    def get_counterexample_prompt(self, **kwargs):
        return _counterexample_prompt.format(**kwargs)
    
    def get_function_debug_prompt(self, **kwargs):
        return _function_debug_prompt.format(**kwargs)

    def get_solution_debug_prompt(self, **kwargs):
        return _solution_debug_prompt.format(**kwargs)

    def get_code_description(self, **kwargs):
        return _code_description.format(**kwargs)

    
_background = """You are an expert of Python programming language. """

_pretest_prompt = """-----Question-----
{question}
-----Task-----
Give an input-output example of the question.
Your output should be in the following format:

-----Input-----
```
Input
```
(Explanation for input if need)

-----Output-----
```
Output
```
(Explanation for input if need)

"""

_solution_debug_prompt = """-----Question-----
{question}
-----Solution-----
{solution}
-----Task-----
The solution failed to pass the following input-output testcase.

-----Input-----
{inputs}
-----Output-----
{outputs}

Give the correct high-level solution which can pass the input-output testcase mentioned above and I/O descriptions.
You should only output fixed high-level solution and I/O descriptions for this problem. You shouldn't output any pseudocode or code.
"""

_function_debug_prompt = """-----Question-----
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
There are some mistakes or exceptions in the function, return the fixed function. You can define helper functions before it to decompose it into sub-functions.
Your output should be in the following format:
```
def {func_name}(...):
    '''
    The description of the function.
    '''
```
You should only output the function code! Omit explanations or any additional text!
"""

_counterexample_prompt = """-----Question-----
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
(Explanation for input if need)

-----Output-----
```
Output
```
(Explanation for input if need)

"""

_solution_prompt = """-----Question-----
{question}

-----Task-----
Propose a clever and efficient high-level solution for this problem. Consider all edge cases and failure modes.

Some common strategies include:
    Constructive algorithms, Binary search, Depth-first search (DFS) and similar algorithms, Dynamic programming, Bitmasks, Brute force, Greedy algorithms, Graphs, Two pointers, Trees, Geometry, Graph matchings, Hashing, Probabilities, Data structures, Sortings, Games, Number theory, Combinatorics, Divide and conquer, Disjoint set union (DSU), Expression parsing

Let's think step by step to come up with a clever algorithm.
You should only output high-level solution without any pseudocode or code.
"""

_translation_prompt = """-----Question-----
{question}

-----Solution-----
{solution}

-----Task-----
Translate the solution for the problem into python code wrapped by ```, which must have one {func_name} function with docstring and implementation, and other functions should only be described by docstring, omit their implementations.

"""

_code_description = """Omit explanations or any additional text."""

