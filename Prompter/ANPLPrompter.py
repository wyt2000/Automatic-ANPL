from .Prompter import AbstractPrompter

class ANPLPrompter(AbstractPrompter):
    
    def get_background(self, **kwargs):
        return _background.format(**kwargs)

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

    
_background = """You are an expert of programming language with significant prior experience in competitive programming. """

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

_function_debug_prompt = """Here is a high-level solution of a programming competition problem.
-----Solution-----
{solution}

Here is an program implementation of the solution.
-----Program-----
{program}

Here is a function of the program with input-output traces. 
-----Function-----
{function_with_traces}

-----Task-----
There are some mistakes or exceptions in the function, return the fixed function. You can define helper functions before it to decompose.
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
The following are examples of ANPL programming language:

# Here is an example of the format applied to identifying the winner of the following game:
# It is so boring in the summer holiday, isn't it? So Alice and Bob have invented a new game to play. The rules are as follows. First, they get a set of n distinct integers. And then they take turns to make the following moves. During each move, either Alice or Bob (the player whose turn is the current) can choose two distinct integers x and y from the set, such that the set doesn't contain their absolute difference |x - y|. Then this player adds integer |x - y| to the set (so, the size of the set increases by one).
# If the current player has no valid move, he (or she) loses the game. The question is who will finally win the game and how many times he moves if both players play optimally. Remember that Alice always moves first.
# Input: The first line is the number of the integers, the second line is the integers.
# Output: The first line is the winner's name, and the second line is the number of moves.
```
def parse_input(input_str: str) -> list[int]:
    '''
    Takes a string containing the length on the first line and the integers on the second and returns the list of integers.
    '''
def all_gcd(l: list[int]) -> int:
    '''
    Returns the greatest common divisor of all elements in the list.
    '''

def num_moves(l: list[int], gcd: int) -> int:
    '''
    The number of moves is the largest element in the list divided by the greatest common divisor of all elements in the list, minus the length of the list. Return the the number of moves.
    '''

def to_output_str(num_moves: int) -> str:
    '''
    Returns a multi-line string. The first line is 'Alice' if the number of moves is odd and 'Bob' if the number of moves is even, the second line is the number of moves.
    '''

def main(input_str: str) -> str:
    '''
    Returns the winner of the game and the number of moves.
    '''
    input_list = parse_input(input_str)
    moves_count = num_moves(input_list, all_gcd(input_list))
    return to_output_str(moves_count)
```

# Here is an example of the format applied to finding a biggest number according to some rules:
```
def parse_input(input_str: str) -> str:
    '''
    Takes a string containing the number of towers on the first line and the heights of the towers on the second and returns the list of heights.
    '''

def side_ones(heights_list: list[int]) -> list[int]:
    '''
    From a list of ints, set the first and last elements to 1 and return the list.
    '''

def destroy_from_left(side_list: list[int]) -> list[int]: 
    '''
    Copy the list and set each each element to the minimum of itself and one more than the element to its left, starting from the second element.
    '''

def destroy_from_right(side_list: list[int]) -> list[int]:
    '''
    Copy the list and set each each element to the minimum of itself and one more than the element to its right, starting from the second to last element.
    '''

def min_list(l1: list[int], l2: list[int]) -> list[int]:
    '''
    Return a list of the minimum of the corresponding elements of l1 and l2.
    '''

def to_output_str(num_moves: list[int]) -> str:
    '''
    Return the string representation of the maximum element in the list.
    '''

def main(input_str: str) -> str:
    '''
    Returns the maximum element after operations.
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

# You should return ANPL code consist with ANPL grammar mentioned above, which must have one main function with implementation.
"""


_code_description = """Omit explanations or any additional text."""

