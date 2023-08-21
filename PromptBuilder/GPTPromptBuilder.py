from .PromptBuilder import AbstractPromptBuilder 

_background = """You are an expert of Python with significant prior experience in competitive programming."""

_solution_prompt = """{question}
-----Solution-----

Propose a clever and efficient high-level solution for this problem. Consider all edge cases and failure modes.

Some common strategies include:
    Constructive algorithms, Binary search, Depth-first search (DFS) and similar algorithms, Dynamic programming, Bitmasks, Brute force, Greedy algorithms, Graphs, Two pointers, Trees, Geometry, Graph matchings, Hashing, Probabilities, Data structures, Sortings, Games, Number theory, Combinatorics, Divide and conquer, Disjoint set union (DSU), Expression parsing

    Write out your reasoning first, and then describe your high-level solution and explain why it is correct.
    \"\"\"
    Let's think step by step to come up with a clever algorithm."""

_translation_prompt = """-----Translation-----
Translate the follwing solution plan into Python code:
\"\"\"
{solution_plan}
\"\"\"
"""

_code_description = """You should only return the pure code. Omit explanations or any additional text. """

_io_description = """Your code should handle the inputs from stdin, and print the output to stdout, so you should return the fullcode including the part handles I/O."""

_start_code = """Your code should start with {starter_code}."""

class GPTPromptBuilder(AbstractPromptBuilder):

    def __init__(self):
        self.clear()

    @property
    def background(self):
        return _background

    def build_solution_request(self, question):
        msg = _solution_prompt.replace("{question}", question)
        self.message.append({"role": "user", "content": msg})
        return self.message
    
    def build_translation_request(self, solution_plan, starter_code):
        msg = _translation_prompt.replace("{solution_plan}", solution_plan)
        if starter_code:
            msg += _starter_code.replace("{starter_code}", starter_code)
        else:
            msg += _io_description
        msg += _code_description
        self.message.append({"role": "user", "content": msg})
        return self.message
    
    def extract_code(self, code: str):
        return code.strip('```python')

   
