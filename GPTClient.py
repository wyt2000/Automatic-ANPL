import openai
import logging 
import logging.config
import aiohttp
import pathlib
import json
from PromptBuilder.PromptBuilder import AbstractPromptBuilder

class GPTClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def request(self, task_name, model_name, question, starter_code, save_dir, prompt_builder: AbstractPromptBuilder):
        prompt_builder.clear()
        # Solution Stage
        messages = prompt_builder.build_solution_request(question)
        self.logger.debug(f'{task_name}: Requesting for high-level solution from {model_name}...')
        response = openai.ChatCompletion.create(
                model       = model_name,
                messages    = messages,
                temperature = 0.6
        )
        solution_plan = prompt_builder.get_response(response)
        self.logger.debug(f'{task_name}: Requesting for high-level solution done!')
        # Translation Stage
        messages = prompt_builder.build_translation_request(solution_plan, starter_code)
        self.logger.debug(f'{task_name}: Requesting for code from {model_name}...')
        response = openai.ChatCompletion.create(
                model            = model_name,
                messages         = messages,
                temperature      = 0.2,
                presence_penalty = 0.1
        )
        code = prompt_builder.get_response(response)
        code = prompt_builder.extract_code(code)
        self.logger.debug(f'{task_name}: Requesting for code solution done!')
        with open(pathlib.Path(save_dir, f'{task_name}.py'), 'w') as f:
            f.write(code)
        return code

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    from PromptBuilder.GPTPromptBuilder import GPTPromptBuilder 
    from ProblemSampler.APPSProblemSampler import APPSProblemSampler
    client = GPTClient()
    sampler = APPSProblemSampler()
    builder = GPTPromptBuilder()
    from utils import mkdir_override
    save_dir = 'test_GPTClient/'
    mkdir_override(save_dir)

    for data in sampler.sample_from_head(2):
        client.request(
            task_name       = f'apps_{data.problem_id}',
            model_name      = 'gpt-3.5-turbo-0301',
            question        = data.question,
            starter_code    = data.starter_code, 
            save_dir        = save_dir,
            prompt_builder  = builder
        )
