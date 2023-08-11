import os
import pathlib
import importlib
import json
import dataclasses
import timeout_decorator
import traceback

from ProgramSampler import ProgramSampler 
from GPTClient import GPTClient 
from ANPLSynthesizer import ANPLSynthesizer
from ANPLPromptWrapper import ANPLPromptWrapper
from ANPLResponseWrapper import ANPLResponseWrapper
from ParselSynthesizer import ParselSynthesizer
from ParselPromptWrapper import ParselPromptWrapper 
from ParselResponseWrapper  import ParselResponseWrapper 
from utils import mkdir_override
from JudgeSystem import JudgeSystem, JudgeError

time_limit = 10

def test_synthesizer(sampler,
                  client,
                  prompt_wrapper,
                  response_wrapper,
                  synthesizer,
                  model_name,
                  prompt_dir,
                  response_dir,
                  result_dir,
                  judge_status_path):
    try:
        mkdir_override(response_dir)
        mkdir_override(result_dir)
        judge_system = JudgeSystem(synthesizer)

        for i, data in enumerate(sampler.dataset):
            task_name = f"{synthesizer.name}_{data.prog_name}"
            print(f'{task_name}: requesting for {model_name}...')
            try:
                response = client.request(model_name,
                                          data.func_name,
                                          data.prompt, 
                                          os.path.join(response_dir, f"{task_name}.res"),
                                          prompt_wrapper,
                                          response_wrapper)
            except Exception:
                print(f'{task_name}: Unknown error occurs during requesting for ChatGPT!')
                traceback.print_exc()
                judge_system.add_judge_status('JudgeUnknownError', data)
                continue
            print(f'{task_name} request for {model_name} done!, the response {synthesizer.name} code is:\n{response}')
            save_path = os.path.join(result_dir, f"{task_name}.py")
            try:
                func = judge_system.compile(response, save_path, data)
                judge_system.judge(func, data.specs, data.func_name)
                print(f'{task_name}: Accepted!')
                judge_system.add_judge_status("JudgeAccepted", data)
            except JudgeError as err:
                print(f'{task_name}: {str(err)}')
                judge_system.add_judge_status(type(err).__name__, data)
                continue
            except Exception:
                print(f'{task_name}: Unknown error occurs during judging!')
                traceback.print_exc()
                judge_system.add_judge_status('JudgeUnknownError', data)
                continue
    finally:
        with open(judge_status_path, 'w') as f:
            f.write(json.dumps(dataclasses.asdict(judge_system.judge_status_container)))

if __name__ == '__main__':

    for num_snippets in range(3, 8):
        sampler = ProgramSampler()
        sampler.sample(
            num_snippets=num_snippets,
            program_dir=f'programs_{num_snippets}/',
            program_prefix=f'string_manipulation_{num_snippets}',
            prompt_dir=f'prompts_{num_snippets}/',
            seed=int(f'{num_snippets}114514')
        )
        client = GPTClient()

        anpl_prompt_wrapper = ANPLPromptWrapper()
        anpl_response_wrapper = ANPLResponseWrapper()
        anpl_synthesizer = ANPLSynthesizer(max_try_times=5, max_temperature=0.5)

        test_synthesizer(
            sampler=sampler,
            client=client,
            prompt_wrapper=anpl_prompt_wrapper,
            response_wrapper=anpl_response_wrapper,
            synthesizer=anpl_synthesizer,
            model_name='gpt-3.5-turbo-0301',
            prompt_dir=f'prompts_{num_snippets}/',
            response_dir=f'anpl_responses_{num_snippets}/',
            result_dir=f'anpl_results_{num_snippets}/',
            judge_status_path=f'anpl_judge_status_{num_snippets}.json',
        )
        
        parsel_prompt_wrapper = ParselPromptWrapper()
        parsel_response_wrapper = ParselResponseWrapper()
        parsel_synthesizer = ParselSynthesizer()

        test_synthesizer(
            sampler=sampler,
            client=client,
            prompt_wrapper=parsel_prompt_wrapper,
            response_wrapper=parsel_response_wrapper,
            synthesizer=parsel_synthesizer,
            model_name='gpt-3.5-turbo-0301',
            prompt_dir=f'prompts_{num_snippets}/',
            response_dir=f'parsel_responses_{num_snippets}/',
            result_dir=f'parsel_results_{num_snippets}/',
            judge_status_path=f'parsel_judge_status_{num_snippets}.json',
        )

