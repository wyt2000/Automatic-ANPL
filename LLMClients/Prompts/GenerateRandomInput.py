GenerateRandomInput = """-----Function-----
{function}

-----Input Constraint-----
{constraint}

-----Task-----
Give a test generator function to generate one random test input for the function with the input constraint mentioned above.
Your output should be in the following format:
```
def test_{func_name}(seed: int) -> list:
    import random
    random.seed(seed)
    (Randomly generate one test input for the function {func_name})
    return inputs # args of {func_name}

def test():
    inputs = test_{func_name}(42)
    outputs = {func_name}(*args)
```

You should only output the python code! Omit explanations or any additional text!
"""
