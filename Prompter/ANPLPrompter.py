from .Prompter import AbstractPrompter

class ANPLPrompter(AbstractPrompter):
    
    def get_background(self, **kwargs):
        return _background.format(**kwargs)

    def get_solution_prompt(self, **kwargs):
        return _solution_prompt.format(**kwargs)

    def get_translation_prompt(self, **kwargs):
        return _translation_prompt.format(**kwargs) + self.get_code_description(**kwargs)

    def get_code_description(self, **kwargs):
        return _code_description.format(**kwargs)

_background = """You are an expert of programming language with significant prior experience in competitive programming. """

_solution_prompt = """Question:
{question}
-----Solution-----

Propose a clever and efficient high-level solution for this problem. Then describe the input-output format consist with the question description. Consider all edge cases and failure modes.

Some common strategies include:
    Constructive algorithms, Binary search, Depth-first search (DFS) and similar algorithms, Dynamic programming, Bitmasks, Brute force, Greedy algorithms, Graphs, Two pointers, Trees, Geometry, Graph matchings, Hashing, Probabilities, Data structures, Sortings, Games, Number theory, Combinatorics, Divide and conquer, Disjoint set union (DSU), Expression parsing

Let's think step by step to come up with a clever algorithm.
You should only output high-level solution and I/O descriptions for this problem. You shouldn't output any pseudocode or code.
"""

_translation_prompt = """
The following are examples of Anpl programming language, ANPL is a special Python code that allows non-main functions to be described with docstrings without implementation. Following the syntax of the example given, the ANPL code for the last question is given.
Note that in the syntax of anpl, the main function must have a function implementation, not just a docstring.
anpl does not support the syntax of classes and objects, so class is not allowed to be used in anpl programs.
-----Translation-----
#  here is an example identifying the largest binary number according to some rules:
```
def remove_zero(binary_str: str) -> str:
    '''
    Remove the first zero from the input string.
    '''

def parse_input(input_str: str) -> str:
    '''
    Takes a string and returns the input string.
    '''

def to_output_str(bigger_str) -> str:
    '''
    Returns the bigger string.
    '''

def main(input_str: str) -> str:
    '''
    Returns the largest binary number that can be made by removing at most one digit from the input string.
    '''
    b_str = parse_input(input_str)
    b_str = remove_zero(b_str)
    return to_output_str(b_str)
```

# Here is an example of the format applied to identifying the winner of a game:
```
def parse_input(input_str: str) -> list[int]:
    '''
    Takes a string containing the length on the first line and the integers on the second and returns the list of integers.
    '''

def num_moves(l: list[int]) -> int:
    '''
    The number of moves is the largest element in the list divided by the greatest common divisor of all elements in the list, minus the length of the list. Return the the number of moves.
    '''

def to_output_str(num_moves: int) -> str:
    '''
    Returns the string 'Alice' if the number of moves is odd and 'Bob' if the number of moves is even.
    '''

def main(input_str: str) -> str:
    '''
    Returns the winner of the game.
    '''
    input_list = parse_input(input_str)
    moves_count = num_moves(input_list)
    return to_output_str(moves_count)
```

# Here is an example of the format applied to finding a biggest number according to some rules:
```
def parse_input(input_str):
    '''
    Takes a string containing the number of towers on the first line and the heights of the towers on the second and returns the list of heights.
    '''

def side_ones(heights_list):
    '''
    From a list of ints, set the first and last elements to 1 and return the list.
    '''

def destroy_from_left(side_list): 
    '''
    Copy the list and set each each element to the minimum of itself and one more than the element to its left, starting from the second element.
    '''

def destroy_from_right(side_list):
    '''
    Copy the list and set each each element to the minimum of itself and one more than the element to its right, starting from the second to last element.
    '''

def min_list(l1, l2):
    '''
    Return a list of the minimum of the corresponding elements of l1 and l2.
    '''

def to_output_str(num_moves):
    '''
    Return the string representation of the maximum element in the list.
    '''

def main(input_str):
    '''
    Returns the winner of the game.
    '''
    heights_list = parse_input(input_str)
    slist = side_ones(heights_list)
    l1 = destroy_from_left(slist)
    l2 = destroy_from_right(slist)
    ans_list = min_list(l1, l2)
    return to_output_str(ans_list)
```

# Translate the following solution plan into the above format:
{solution}
"""


_code_description = """Omit explanations or any additional text."""

