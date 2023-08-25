from .Prompter import AbstractPrompter

class GPTPrompter(AbstractPrompter):
    
    def get_background(self, **kwargs):
        return _background.format(**kwargs)

    def get_solution_prompt(self, **kwargs):
        return _solution_prompt.format(**kwargs)

    def get_translation_prompt(self, **kwargs):
        return _translation_prompt.format(**kwargs) + self.get_code_desciption(**kwargs)

    def get_code_description(self, starter_code="", **kwargs):
        desc = _code_description.format(**kwargs)
        if starter_code:
            desc += _starter_code.format(starter_code=starter_code)
        else:
            desc += _io_description
        return desc

_background = """You are an expert of Python with significant prior experience in competitive programming."""

_solution_prompt = """Question:
{question}
-----Solution-----

Propose a clever and efficient high-level solution for this problem. Consider all edge cases and failure modes.

Some common strategies include:
    Constructive algorithms, Binary search, Depth-first search (DFS) and similar algorithms, Dynamic programming, Bitmasks, Brute force, Greedy algorithms, Graphs, Two pointers, Trees, Geometry, Graph matchings, Hashing, Probabilities, Data structures, Sortings, Games, Number theory, Combinatorics, Divide and conquer, Disjoint set union (DSU), Expression parsing

Write out your reasoning first, and then describe your high-level solution and explain why it is correct.
\"\"\"
Let's think step by step to come up with a clever algorithm.
Your response should contains at most 1000 tokens.
"""

_translation_prompt = """-----Translation-----
Translate the follwing solution plan into Python code:
\"\"\"
{solution}
\"\"\"
"""

_code_description = """You should only return the pure code. Omit explanations or any additional text. """

_starter_code = """Your code should start with {starter_code}."""

_io_description = """Your code should handle the inputs from stdin, and print the output to stdout, so you should return the fullcode including the part handles I/O."""


