GenerateFunctionWithAsserts = """{prefix}
Here is a python program: 
-----Program-----
```
{code}
```

Here is an unimplemented function of the program:
-----Function-----
```
{hole}
```

-----Task-----
1. Complete the function.
2. Add docstring to describe the new function you generated if it doesn't have one.
3. Insert assert statements between lines of the function to do the property testing.
Your output should be in the following format:
```
def {func_name}(...):
    "The description of the function."
```

"""
