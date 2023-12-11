GenerateCounterexample = """-----Question-----
{question}

-----Program-----
{program}

-----Task-----
Give an assert test for the question to find hidden bugs in the program. Each assert statement should be on one line.
Your output should be in the following format:
```
assert 
```

You should only output the assert test. Omit explanations or any additional text.
"""
