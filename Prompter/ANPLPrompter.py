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
The following are examples of ANPL programming language:
# Here is an example identifying the largest binary number according to some rules:
# The Little Elephant has an integer a, written in the binary notation. He wants to write this number on a piece of paper.
# To make sure that the number a fits on the piece of paper, the Little Elephant ought to delete exactly one any digit from number a in the binary record. At that a new number appears. It consists of the remaining binary digits, written in the corresponding order (possible, with leading zeroes).
# The Little Elephant wants the number he is going to write on the paper to be as large as possible. Help him find the maximum number that he can obtain after deleting exactly one binary digit and print it in the binary notation.
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

def num_moves(l: list[int]) -> int:
    '''
    The number of moves is the largest element in the list divided by the greatest common divisor of all elements in the list, minus the length of the list. Return the the number of moves.
    '''
    mx = max(l)
    ans = mx // all_gcd(l) - len(l)
    return ans

def to_output_str(num_moves: int) -> str:
    '''
    Returns a multi-line string. The first line is 'Alice' if the number of moves is odd and 'Bob' if the number of moves is even, the second line is the number of moves.
    '''

def main(input_str: str) -> str:
    '''
    Returns the winner of the game and the number of moves.
    '''
    input_list = parse_input(input_str)
    moves_count = num_moves(input_list)
    return to_output_str(moves_count)
```

# Here is an example of the format applied to finding a biggest number according to the rules:
# Limak is a little bear who loves to play. Today he is playing by destroying block towers. He built n towers in a row. The i-th tower is made of h_i identical blocks. For clarification see picture for the first sample.
# Limak will repeat the following operation till everything is destroyed.
# Block is called internal if it has all four neighbors, i.e. it has each side (top, left, down and right) adjacent to other block or to the floor. Otherwise, block is boundary. In one operation Limak destroys all boundary blocks. His paws are very fast and he destroys all those blocks at the same time.
# Limak is ready to start. You task is to count how many operations will it take him to destroy all towers.
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


# You should return ANPL code consist with ANPL grammar mentioned above, which must have one main function with implementation.
"""


_code_description = """Omit explanations or any additional text."""

