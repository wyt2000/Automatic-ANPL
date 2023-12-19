GenerateValidator = """-----Function-----
{function}

-----Task-----
Give a validator function to validate the correctness of the function mentioned above. Consider all edge cases and failure modes.
Your output should be in the following format:
```
def validate_{func_name}(...): # Same as inputs of {func_name}
    outputs = {func_name}(...)
    (Check the correctness of the outputs, raise Exception if fail)
```

"""
