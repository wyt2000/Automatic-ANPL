from .Prompter import AbstractPrompter

class ParselPrompter(AbstractPrompter):
    
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
The following are examples of Parsel programming language:
# Here is an example calculating the probability of landing on the same character in a random shift of an input string, based on the following problem:
# Vasya and Kolya play a game with a string, using the following rules. Initially, Kolya creates a string s, consisting of small English letters, and uniformly at random chooses an integer k from a segment [0, len(s) - 1]. He tells Vasya this string s, and then shifts it k letters to the left, i.e. creates a new string t = s_k + 1s_k + 2... s_ns_1s_2... s_k. Vasya does not know the integer k nor the string t, but he wants to guess the integer k. To do this, he asks Kolya to tell him the first letter of the new string, and then, after he sees it, open one more letter on some position, which Vasya can choose.
# Vasya understands, that he can't guarantee that he will win, but he wants to know the probability of winning, if he plays optimally. He wants you to compute this probability.
# Note that Vasya wants to know the value of k uniquely, it means, that if there are at least two cyclic shifts of s that fit the information Vasya knowns, Vasya loses. Of course, at any moment of the game Vasya wants to maximize the probability of his win.
\"\"\"
generate_cyclic_shifts(input_str: str) -> str: Calculates the average number of unique characters in the substrings of the input string that start with each character. Parse input_str, then call compute_a_and_letter_pos and pass the return value to compute_unique_characters to get the answer. Convert answer to str and return it.
    parse_input(input_str: str) -> str: Takes a string and returns the input string
    compute_a_and_letter_pos(input_str: str) -> (list[int], list[list[int]]): Generates the str_as_number_list and letter_pos lists. str_as_number_list is a list of integers that is used to store the character values of the input string. str_as_number_list is initialized as a list of 0s for twice the length of the input string. The values are calculated by taking the ASCII value of each character in the string and subtracting the ASCII value of the character 'a'. letter_pos is a list of lists, with each sublist containing the indices at which a particular character appears in the input string.
    compute_unique_characters(c: str, str_as_number_list: list[int], letter_pos: list[list[int]]) -> list[int]: Calculates the maximum number of unique characters in all substrings (for k=1 to length) that start with the character represented by c. letter_pos is a list of lists, with each sublist containing the indices at which a character appears in the input string. str_as_number_list is a list of integers that is used to store the character values of the input string.
        compute_unique_characters_for_k(c: str, k: int, str_as_number_list: list[int], letter_pos: list[list[int]]) -> int: Create a counts list of zeros for each of the 26 alphabetical characters. For each i in the sublist of positions of letter_pos[c], increment counts at str_as_number_list[i + k]. Return the number of counts which are exactly one.
    to_output_str(ans: list[int], input_str: str) -> str: Returns a string representation of ans divided by the length of the input string.
\"\"\"

# And here is an example identifying the largest binary number according to the following rules:
# The Little Elephant has an integer a, written in the binary notation. He wants to write this number on a piece of paper.
# To make sure that the number a fits on the piece of paper, the Little Elephant ought to delete exactly one any digit from number a in the binary record. At that a new number appears. It consists of the remaining binary digits, written in the corresponding order (possible, with leading zeroes).
# The Little Elephant wants the number he is going to write on the paper to be as large as possible. Help him find the maximum number that he can obtain after deleting exactly one binary digit and print it in the binary notation.
\"\"\"
largest_binary_number(input_str: str) -> str: Returns the largest binary number that can be made by removing at most one digit from the input string. 
    parse_input(input_str: str) -> str: Takes a string and returns the input string
    remove_zero(binary_str: str) -> str: Remove the first zero from the input string.
    to_output_str(bigger_str: str) -> str: Returns the bigger string.
\"\"\"

# Here is an example of the format applied to identifying the winner of the following game:
# It is so boring in the summer holiday, isn't it? So Alice and Bob have invented a new game to play. The rules are as follows. First, they get a set of n distinct integers. And then they take turns to make the following moves. During each move, either Alice or Bob (the player whose turn is the current) can choose two distinct integers x and y from the set, such that the set doesn't contain their absolute difference |x - y|. Then this player adds integer |x - y| to the set (so, the size of the set increases by one).
# If the current player has no valid move, he (or she) loses the game. The question is who will finally win the game and how many times he moves if both players play optimally. Remember that Alice always moves first.
# Output: The first line is the winner's name, and the second line is the number of moves.
\"\"\"
identify_winner(input_str: str) -> str: Parse the input to list and call num_moves to get the number of moves. Return to_output_str(num_moves). 
    parse_input(input_str: str) -> list[int]: Takes a string containing the length on the first line and the integers on the second and returns the list of integers
    num_moves(l: list[int]) -> int: The number of moves is the largest element in the list divided by the greatest common divisor of all elements in the list, minus the length of the list.
        all_gcd(l: list[int]) -> int: Returns the greatest common divisor of all elements in the list
    to_output_str(num_moves: int) -> str: Returns a multi-line string. The first line is 'Alice' if the number of moves is odd and 'Bob' if the number of moves is even, the second line is the number of moves.
\"\"\"

# Translate the following solution plan into the above format:
{solution}

# You should return Parsel code consist with Parsel grammar mentioned above, whose functions are defined by natural language in only one single line for each function! 

# There should be only one top function in Parsel code, which has no indentation.

# The natural language definition of the top function should be I/O descriptions of the program and calling relationships of other functions. It shouldn't be empty!

# You shouldn't output any Python code! You shouldn't copy the examples above!
"""

_code_description = """Omit explanations or any additional text."""

