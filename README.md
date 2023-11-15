# Program-Synthetic-AutoTester

## TODO

- Add CI to ensure code modifications are correct.
    - How to do tests? Unit tests (like Tracer) + requests for HumanEval and check accuracy.
    - Small ranges limited by github and openai.
    - Fix args in `solve.py`.
- Remove Useless codes.
    - Refactor the string generation tests in main branch.
- GPTClient and Prompters.
    - Unify api.
- ANPL.
    - Merge utils and helpers, delete duplicated codes.
    - Merge Tracer, fix bug in synthesizer.
    - Separate debug logic, merge sample code in synthesizer and debugger.
    - Refactor evaluation to support all types of IOs.
- Support pass@k mode (eval by generated tests) and pass@any mode (eval by real tests).
- Concurrently request for GPT, reach tokens rate limit.
