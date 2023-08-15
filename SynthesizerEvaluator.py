import os
import traceback
import json
import dataclasses
import logging
import asyncio
from GPTClient import GPTClient
from JudgeSystem import JudgeSystem, JudgeStatus, JudgeAccepted, JudgeUnknownError
from utils import color_str

class SynthesizerEvaluator:
    '''
    Main class of the project.
    '''

    def __init__(self,
                 synthesizer,
                 prompt_wrapper,
                 response_wrapper,
                 model_name,
                 response_dir,
                 result_dir,
                 log_dir
                 ):
        '''
        :param synthesizer: Subclass of `AbstarctSynthesizer`, method `synthesize` should be implemented.
        :type synthesizer: Synthesizer

        :param prompt_wrapper: Subclass of `AbstarctPromptWrapper`, proporty `background`, `pre_prompt` and `post_prompt` should be implemented.
        :type prompt_wrapper: PromptWrapper

        :param response_wrapper: Subclass of `AbstractResponseWrapper`, method `wrap` should be implemented.
        :type response_wrapper: ResponseWrapper

        :param model_name: GPT model name.
        :type model_name: str

        :param response_dir: Folder path to save ChatGPT responses, should ensure it exists.
        :type response_dir: str

        :param result_dir: Folder path to save target code generated by the synthesizer, should ensure it exists.
        :type result_dir: str

        :param log_dir: Folder path to save synthesizer's log.
        :type log_dir: str
        '''

        self.synthesizer        = synthesizer
        self.prompt_wrapper     = prompt_wrapper
        self.response_wrapper   = response_wrapper
        self.model_name         = model_name
        self.response_dir       = response_dir
        self.result_dir         = result_dir
        self.log_dir            = log_dir
        self.client             = GPTClient() 
        self.judge_system       = JudgeSystem(self.synthesizer) 
        self.logger             = logging.getLogger(__name__)

    async def evaluate(self, task_name, data, semaphone):
        '''
        Evaluate the synthesizer by one piece of data, including:
        1. Request ChatGPT for the synthesizer's DSL by wrapped prompts.
        2. Synthesize the DSL to generate target code, which can be called as `compile`.
        3. Judge whether the target code can satisfy the I/O specs in data.
        The result will be raised as `JudgeStatus` exception, just like status in common online judges.
        
        :param task_name: Identify the synthesizer and the data, used in log.
        :type task_name: str

        :param data:
        :type data: ProgramData

        :param semaphone: Semaphone to control coroutine number.
        :type semaphone: asyncio.Semaphore

        :raise JudgeAccepted: The program passed all I/O spec tests.
        :raise JudgeWrongAnswer: The program failed at some I/O spec test.
        :raise JudgeTimeLimitExceeded: The program was executed for too long time, the time limit can be set in `judge_system`.
        :raise JudgeRuntimeError: The program crashed during being executed. 
        :raise JudgeCompileError: Error occured during synthesizing or getting target code. 
        :raise JudgeUnknownError: Other strange errors, eg: ChatGPT crashed.
        '''
        async with semaphone:
            try:
                response = await self.client.request(
                                          task_name,
                                          self.model_name,
                                          data.func_name,
                                          data.prompt, 
                                          os.path.join(self.response_dir, f"{task_name}.res"),
                                          self.prompt_wrapper,
                                          self.response_wrapper)
            except Exception :
                self.logger.exception("Exception")
                raise JudgeUnknownError(color_str("Unknown error occurs during requesting for ChatGPT!", "red"))
            self.logger.debug(f'The response {self.synthesizer.name} code is:\n{response}')
            save_path = os.path.join(self.result_dir, f"{task_name}.py")
            func = self.judge_system.compile(response, save_path, data, os.path.join(self.log_dir,f"{task_name}.log"))
            self.judge_system.judge(func, data.specs, data.func_name)
            raise JudgeAccepted(color_str("Accepted!", "green"))

    def clear(self):
        '''
        Clear judge status.
        '''
        self.judge_system.clear()

    def evaluate_all(self, dataset, num_workers=8):
        '''
        Evaluate the synthesizer by dataset, save the results in `judge_status_path`.
        :param dataset:
        :type dataset: list[ProgramData]

        :param num_workers: Concurrent task number.
        :type num_workers: int
        '''
        semaphone = asyncio.Semaphore(num_workers)
        async def batch_tasks():
            tasks = []
            for data in dataset:
                task_name = f"{self.synthesizer.name}_{data.prog_name}"
                tasks.append((task_name, data, asyncio.create_task(self.evaluate(task_name, data, semaphone))))
            for task_name, data, task in tasks:
                try:
                    await task
                except JudgeStatus as status:
                    self.logger.info(f'{task_name}: {str(status)}')
                    self.judge_system.add_judge_status(type(status).__name__, data)
                except Exception:
                    self.logger.exception(f'{task_name}: ' + color_str('Unknown error occurs during judging!', 'red'))
                    self.judge_system.add_judge_status("JudgeUnknownError", data)
        asyncio.run(batch_tasks())

