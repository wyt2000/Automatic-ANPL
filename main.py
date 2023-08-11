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

time_limit = 10

@dataclasses.dataclass
class CompileInfo:
    compiler_name : str = 'anpl'
    compile_errors : dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    time_limit_exceededs: dict[str, int] = dataclasses.field(default_factory=dict) 
    runtime_errors: dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    accepteds : dict[str, int] = dataclasses.field(default_factory=dict) 

def test_synthesizer(sampler,
                  client,
                  prompt_wrapper,
                  response_wrapper,
                  synthesizer,
                  model_name,
                  prompt_dir,
                  response_dir,
                  result_dir,
                  compile_info_path):
    try:
        mkdir_override(response_dir)
        mkdir_override(result_dir)
        compile_info = CompileInfo(synthesizer.name)

        for i, data in enumerate(sampler.dataset):
            try:
                task_name = f"{synthesizer.name}_{data.prog_name}"
                print(f'{task_name}: requesting for {model_name}...')
                response = client.request(model_name,
                                          data.func_name,
                                          data.prompt, 
                                          os.path.join(response_dir, f"{task_name}.res"),
                                          prompt_wrapper,
                                          response_wrapper)
                print(f'{task_name} request for {model_name} done!, the response {synthesizer.name} code is:\n{response}')
                code_path = os.path.join(result_dir, f"{task_name}.py")
                try:
                    code = synthesizer.synthesize(response, code_path, data.prog_name)
                except Exception as err:
                    print(f'{task_name}: synthesis failed!')
                    traceback.print_exc()
                    code = None
                finally:
                    pass
                if code is None:
                    print(f'{task_name}: compile error!')
                    compile_info.compile_errors[data.prog_name] = data.num_snippets
                    continue

                try:
                    module_path = os.path.splitext(code_path)[0]
                    module = importlib.import_module(module_path.replace('/', '.'))
                    func = module.__getattribute__(data.func_name)
                except:
                    print(f'{task_name}: func {data.func_name} not found, compile error!')
                    traceback.print_exc()
                    compile_info.compile_errors[data.prog_name] = data.num_snippets
                    continue
                @timeout_decorator.timeout(time_limit)
                def timeout_func(inp):
                    out = func(inp)
                    return out
                ok = True
                for inp, ans in data.specs:
                    try: 
                        out = timeout_func(inp)
                    except timeout_decorator.TimeoutError as err:
                        print(f'{task_name}: Time limit exceeded at {data.func_name}(\"{inp}\") = \"{ans}\"!')
                        ok = False
                        compile_info.time_limit_exceededs[data.prog_name] = data.num_snippets
                        break
                    except Exception as err:
                        print(f'{task_name}: Runtime error at {data.func_name}(\"{inp}\") = \"{ans}\"!')
                        ok = False
                        compile_info.runtime_errors[data.prog_name] = data.num_snippets
                        break
                    if out != ans: 
                        print(f'{task_name}: Wrong Answer! {data.func_name}(\"{inp}\") should be \"{ans}\"!')
                        ok = False
                        compile_info.wrong_answers[data.prog_name] = data.num_snippets
                        break
                if ok:
                    print(f'{task_name}: Accepted!')
                    compile_info.accepteds[data.prog_name] = data.num_snippets
            except Exception as err:
                print(err)
    finally:
        with open(compile_info_path, 'w') as f:
            f.write(json.dumps(dataclasses.asdict(compile_info)))

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

        #test_synthesizer(
        #    sampler=sampler,
        #    client=client,
        #    prompt_wrapper=anpl_prompt_wrapper,
        #    response_wrapper=anpl_response_wrapper,
        #    synthesizer=anpl_synthesizer,
        #    model_name='gpt-3.5-turbo-0301',
        #    prompt_dir=f'prompts_{num_snippets}/',
        #    response_dir=f'anpl_responses_{num_snippets}/',
        #    result_dir=f'anpl_results_{num_snippets}/',
        #    compile_info_path=f'anpl_compile_info_{num_snippets}.json',
        #)

        
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
            compile_info_path=f'parsel_compile_info_{num_snippets}.json',
        )


