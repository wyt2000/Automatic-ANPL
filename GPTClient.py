import openai
import logging 
import logging.config
import aiohttp
from PromptBuilder.PromptBuilder import AbstractPromptBuilder

logging.config.fileConfig('logging.conf')

class GPTClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def request(self, task_name, model_name, question, starter_code, save_path, prompt_builder: AbstractPromptBuilder):
        prompt_builder.clear()
        # Solution Stage
        messages = prompt_builder.build_solution_request(question)
        self.logger.debug(f'{task_name}: Requesting for high-level solution from {model_name}...')
        response = openai.ChatCompletion.create(model=model_name, messages=messages)
        solution_plan = prompt_builder.get_response(response)
        self.logger.debug(f'{task_name}: Requesting for high-level solution done!')
        # Translation Stage
        messages = prompt_builder.build_translation_request(solution_plan, starter_code)
        self.logger.debug(f'{task_name}: Requesting for Python code from {model_name}...')
        response = openai.ChatCompletion.create(model=model_name, messages=messages)
        code = prompt_builder.get_response(response)
        self.logger.debug(f'{task_name}: Requesting for Python code solution done!')
        with open(save_path, 'w') as f:
            f.write(code)
        return code

if __name__ == '__main__':
    from PromptBuilder.GPTPromptBuilder import GPTPromptBuilder 
    from ProblemSampler.APPSProblemSampler import APPSProblemSampler
    client = GPTClient()
    sampler = APPSProblemSampler()
    builder = GPTPromptBuilder()
    for data in sampler.sample_from_head(2):
        client.request(
            task_name      = f'apps_{data.problem_id}',        
            model_name     = 'gpt-3.5-turbo-0301',
            question       = data.question,
            starter_code   = data.starter_code, 
            save_path      = f'apps_{data.problem_id}.py',
            prompt_builder = builder
        )
