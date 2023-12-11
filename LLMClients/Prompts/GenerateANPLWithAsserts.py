GenerateANPLWithAsserts = """-----Question-----
{question}

-----Solution-----
{solution}

Here is an program implementation of the solution.
-----Program-----
{program}

Here is a function of the program.
-----Function-----
{function}

-----Task-----
Insert assert statements between lines of the function to do the property testing.
Your output should be in the following format:
```
def {func_name}(...):
    "The description of the function."
    (The implementation codes and the asserts between them)
```

You should only output the function code! Omit explanations or any additional text!
"""
