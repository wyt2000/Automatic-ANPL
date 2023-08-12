import os
import traceback
import json
import dataclasses
from JudgeSystem import JudgeSystem, JudgeError

class SynthesizerEvaluator:

    def __init__(self,
                 synthesizer,
                 client,
                 prompt_wrapper,
                 response_wrapper,
                 model_name,
                 response_dir,
                 result_dir
                 ):

        self.synthesizer        = synthesizer
        self.client             = client
        self.prompt_wrapper     = prompt_wrapper
        self.response_wrapper   = response_wrapper
        self.model_name         = model_name
        self.response_dir       = response_dir
        self.result_dir         = result_dir
        self.judge_system       = JudgeSystem(self.synthesizer) 

    def evaluate(self, data):
        task_name = f"{self.synthesizer.name}_{data.prog_name}"
        print(f'{task_name}: requesting for {self.model_name}...')
        try:
            response = self.client.request(self.model_name,
                                      data.func_name,
                                      data.prompt, 
                                      os.path.join(self.response_dir, f"{task_name}.res"),
                                      self.prompt_wrapper,
                                      self.response_wrapper)
        except Exception:
            print(f'{task_name}: Unknown error occurs during requesting for ChatGPT!')
            traceback.print_exc()
            return 'JudgeUnknownError'
        print(f'{task_name} request for {self.model_name} done!, the response {self.synthesizer.name} code is:\n{response}')
        save_path = os.path.join(self.result_dir, f"{task_name}.py")
        try:
            func = self.judge_system.compile(response, save_path, data)
            self.judge_system.judge(func, data.specs, data.func_name)
            print(f'{task_name}: Accepted!')
            return 'JudgeAccepted'
        except JudgeError as err:
            print(f'{task_name}: {str(err)}')
            return type(err).__name__
        except Exception:
            print(f'{task_name}: Unknown error occurs during judging!')
            traceback.print_exc()
            return 'JudgeUnknownError'

    def evaluate_all(self, dataset, judge_status_path):
        self.judge_system.clear()
        try:
            for data in dataset:
                self.judge_system.add_judge_status(self.evaluate(data), data)
        finally:
            with open(judge_status_path, 'w') as f:
                f.write(json.dumps(dataclasses.asdict(self.judge_system.judge_status_container)))

