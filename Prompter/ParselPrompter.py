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

Propose a clever and efficient high-level solution for this problem. Consider all edge cases and failure modes.

Some common strategies include:
    Constructive algorithms, Binary search, Depth-first search (DFS) and similar algorithms, Dynamic programming, Bitmasks, Brute force, Greedy algorithms, Graphs, Two pointers, Trees, Geometry, Graph matchings, Hashing, Probabilities, Data structures, Sortings, Games, Number theory, Combinatorics, Divide and conquer, Disjoint set union (DSU), Expression parsing

Let's think step by step to come up with a clever algorithm.
You should only output exactly high-level solution for this problem. You shouldn't output any pseudocode or code.
"""

_translation_prompt = """
The following are examples of Parsel programming language:
# Here is an example calculating the probability of landing on the same character in a random shift of an input string, based on the following problem:
# Vasya and Kolya play a game with a string, using the following rules. Initially, Kolya creates a string s, consisting of small English letters, and uniformly at random chooses an integer k from a segment [0, len(s) - 1]. He tells Vasya this string s, and then shifts it k letters to the left, i.e. creates a new string t = s_k + 1s_k + 2... s_ns_1s_2... s_k. Vasya does not know the integer k nor the string t, but he wants to guess the integer k. To do this, he asks Kolya to tell him the first letter of the new string, and then, after he sees it, open one more letter on some position, which Vasya can choose.
# Vasya understands, that he can't guarantee that he will win, but he wants to know the probability of winning, if he plays optimally. He wants you to compute this probability.
# Note that Vasya wants to know the value of k uniquely, it means, that if there are at least two cyclic shifts of s that fit the information Vasya knowns, Vasya loses. Of course, at any moment of the game Vasya wants to maximize the probability of his win.
\"\"\"
generate_cyclic_shifts(input_str: str) -> str: Calculates the average number of unique characters in the substrings of the input string that start with each character.
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
# If the current player has no valid move, he (or she) loses the game. The question is who will finally win the game if both players play optimally. Remember that Alice always moves first.
\"\"\"
identify_winner(input_str: str) -> str: Returns the winner of the game.
    parse_input(input_str: str) -> list[int]: Takes a string containing the length on the first line and the integers on the second and returns the list of integers
    num_moves(l: list[int]) -> int: The number of moves is the largest element in the list divided by the greatest common divisor of all elements in the list, minus the length of the list.
        all_gcd(l: list[int]) -> int: Returns the greatest common divisor of all elements in the list
    to_output_str(num_moves: int) -> str: Returns the string 'Alice' if the number of moves is odd and 'Bob' if the number of moves is even
\"\"\"

# Limak is a little bear who loves to play. Today he is playing by destroying block towers. He built n towers in a row. The i-th tower is made of h_i identical blocks. For clarification see picture for the first sample.
# Limak will repeat the following operation till everything is destroyed.
# Block is called internal if it has all four neighbors, i.e. it has each side (top, left, down and right) adjacent to other block or to the floor. Otherwise, block is boundary. In one operation Limak destroys all boundary blocks. His paws are very fast and he destroys all those blocks at the same time.
# Limak is ready to start. You task is to count how many operations will it take him to destroy all towers.
\"\"\"
destroy_towers(input_str: str) -> str: Returns the number of operations it takes to destroy all towers.
    parse_input(input_str: str) -> list[int]: Takes a string containing the number of towers on the first line and the heights of the towers on the second and returns the list of heights
    side_ones(heights_list: list[int]) -> list[int]: From a list of ints, set the first and last elements to 1 and return the list
    destroy_from_left(side_list: list[int]) -> list[int]: Copy the list and set each element to the minimum of itself and one more than the element to its left, starting from the second element
    destroy_from_right(side_list: list[int]) -> list[int]: Copy the list and set each element to the minimum of itself and one more than the element to its right, starting from the second to last element
    min_list(l1: list[int], l2: list[int]) -> list[int]: Return a list of the minimum of the corresponding elements of l1 and l2
    to_output_str(min_list: list[int]) -> str: Return the string representation of the maximum element in the list
\"\"\"

# Alex decided to go on a touristic trip over the country.
# For simplicity let's assume that the country has $n$ cities and $m$ bidirectional roads connecting them. Alex lives in city $s$ and initially located in it. To compare different cities Alex assigned each city a score $w_i$ which is as high as interesting city seems to Alex.
# Alex believes that his trip will be interesting only if he will not use any road twice in a row. That is if Alex came to city $v$ from city $u$, he may choose as the next city in the trip any city connected with $v$ by the road, except for the city $u$.
# Your task is to help Alex plan his city in a way that maximizes total score over all cities he visited. Note that for each city its score is counted at most once, even if Alex been there several times during his trip.
\"\"\"
max_score(input_str: str) -> str: Simple function returning the maximum score Alex can get.
    parse_input(input_str: str) -> (list[int], list[list[int]], int): Takes a string containing the number of cities and roads on one line, the scores of the cities on the next line, the roads on the next lines besides the last (1-indexed, make 0-indexed), and the starting city on the last line. It returns the city scores, the roads as an edge list, and the starting city.
    get_neighbors(edges: list[list[int]]) -> dict[int, list[int]]: Returns a dictionary of the neighbors of each city, defaulting to an empty set.
  get_degrees_and_leaves(neighbors: dict[int, list[int]], root: int) -> (dict[int, int], set[int]): Returns a dictionary of the degrees of each city, and a set of the leaves (excluding the root).
    remove_leaves(scores: list[int], neighbors: dict[int, list[int]], degrees: dict[int, int], leaves: set[int], root: int) -> int: Create a 0-initialized defaultdict of total_extra, and an int of max_extra. Pop leaves until it is empty. Update total_extra and max_extra based on the parent's total_extra vs the leaf's score plus its total_extra, whichever is greater. Return max_extra.
        pop_leaf(neighbors: dict[int, list[int]], degrees: dict[int, int], leaves: set[int], root: int) -> (int, int): Pop off a leaf. Set parent to sole neighbor of the leaf and delete the leaf from the neighbors dictionary. Decrement the parent's degree. If the parent is not the root and has degree 1, add it to the leaves. Return the leaf and parent.
    to_output_str(scores: list[int], neighbors: dict[int, list[int]], root: int, max_extra:int ) -> str: Returns the string of the maximum score Alex can get. If the root isn't in neighbors, return the score of the root. Otherwise, this is the sum of the scores of the cities left in neighbors, plus the returned encountered max_extra.
\"\"\"

# Translate the following solution plan into the above format:
{solution}
# You should return Parsel code consist with Parsel grammar mentioned above, whose functions are defined by natural language in only one single line for each function! There should be only one top function in Parsel code, which has no indentation. You shouldn't output any Python code! You shouldn't copy the examples above!"""

_code_description = """Omit explanations or any additional text."""

