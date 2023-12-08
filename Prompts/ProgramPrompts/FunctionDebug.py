FunctionDebug = """-----Question-----
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
If there are some mistakes or exceptions in the function, return the fixed function. You can define helper functions before it to decompose it into sub-functions.
Your output should be in the following format:
```
def {func_name}(...):
    "The description of the function."
```

You should only output the function code! Omit explanations or any additional text!
"""
