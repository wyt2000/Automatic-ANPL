GenerateANPL = """-----Question-----
{question}

-----Solution-----
{solution}

-----Task-----
Translate the solution for the problem into python code in the following format:

-----Program-----
```
python code
```

You should define some helper functions before function {entry_point} to decompose it. Each function should be described by docstring.
You should only output the python code! Omit explanations or any additional text!
"""
