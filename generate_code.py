from GPTClient import GPTClient
from PromptBuilder.GPTPromptBuilder import GPTPromptBuilder 
from ProblemSampler.APPSProblemSampler import APPSProblemSampler
from utils import mkdir_override
import logging 
import logging.config

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    client = GPTClient()
    sampler = APPSProblemSampler()
    builder = GPTPromptBuilder()

    save_dir = 'gpt_apps_code/'
    mkdir_override(save_dir)
    num_samples = 10

    for data in sampler.sample_from_head(5):
        for i in range(num_samples):
            client.request(
                task_name      = f'gpt_{data.problem_id}_{i}', 
                model_name     = 'gpt-3.5-turbo-0301',
                question       = data.question,
                starter_code   = data.starter_code, 
                save_dir       = save_dir,
                prompt_builder = builder
            )
