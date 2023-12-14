from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler

def test_HumanEvalProblemSampler():
    sampler = HumanEvalProblemSampler()
    dataset = sampler.sample([0])
    for data in dataset:
        assert repr(data) == "HumanEvalProblemData(problem_id=HumanEval_0, entry_point=has_close_elements)"
        assert sorted(data.system_tests) == sorted(['assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True', 'assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True', 'assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True', 'assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False', 'assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False', 'assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False', 'assert has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True'])

