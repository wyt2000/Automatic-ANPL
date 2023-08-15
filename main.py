from ProgramSampler                         import ProgramSampler 
from SynthesizerEvaluator                   import SynthesizerEvaluator
from utils                                  import mkdir_override, make_object
import logging.config
import yaml
import copy 
import json
import dataclasses

logging.config.fileConfig('logging.conf')

class ConfigManager:

    def __init__(self, config_path='config.yml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def _transform_sample_config(self, num_snippets, config):
        new_config = copy.deepcopy(config)
        new_config['num_snippets']      = num_snippets
        new_config['seed']              = int(str(num_snippets) + str(config['seed']))
        new_config['program_prefix']    += f'_{num_snippets}'
        new_config['program_dir']       += f'_{num_snippets}'
        new_config['prompt_dir']        += f'_{num_snippets}'
        return new_config

    def build_program_datasets(self, config):
        sampler = ProgramSampler(input_path=config['input_path'])
        config = config['sample_config']
        if isinstance(config['num_snippets'], int):
            yield sampler.sample(**config)
            return
        for num_snippets in config['num_snippets']:
            yield sampler.sample(**self._transform_sample_config(num_snippets, config))

    def _make_object(self, prefix, config):
        return make_object('.'.join([prefix, config['name']]), config['name'], **config.get('args', {}))

    def build_evaluators(self, syn_configs, suffix):
        for config in syn_configs:
            prompt_wrapper = self._make_object('PromptWrapper', config['prompt_wrapper_class']) 
            response_wrapper = self._make_object('ResponseWrapper', config['response_wrapper_class']) 
            synthesizer = self._make_object('Synthesizer', config['synthesizer_class']) 
            name = config['name']

            response_dir = f'{name}_responses_{suffix}/'
            result_dir = f'{name}_results_{suffix}/'
            log_dir= f'{name}_logs_{suffix}/'

            mkdir_override(response_dir)
            mkdir_override(result_dir)
            mkdir_override(log_dir)

            yield SynthesizerEvaluator(
                synthesizer=synthesizer,
                prompt_wrapper=prompt_wrapper,
                response_wrapper=response_wrapper,
                model_name=config['model_name'],
                response_dir=response_dir,
                result_dir=result_dir,
                log_dir=log_dir
            )

if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    configManager = ConfigManager()
    for config in configManager.config:
        for dataset in configManager.build_program_datasets(config['ProgramSamplerConfig']):
            num_snippets = dataset[0].num_snippets
            for evaluator in configManager.build_evaluators(config['SynthesizerConfig'], suffix=num_snippets):
                judge_status_path = f'{evaluator.synthesizer.name}_judge_status_{num_snippets}.json'
                try:
                    evaluator.evaluate_all(dataset)
                finally:
                    with open(judge_status_path, 'w') as f:
                        f.write(json.dumps(dataclasses.asdict(evaluator.judge_system.judge_status_container)))

