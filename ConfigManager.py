from ProgramSampler                         import ProgramSampler 
from SynthesizerEvaluator                   import SynthesizerEvaluator
from utils                                  import mkdir_override, make_object
import yaml
import copy

class ConfigManager:

    def __init__(self, config_path='config.yml'):
        '''
        Load yaml config.
        :param config_path:
        :type config_path: str
        '''
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
        '''
        Generate program datasets.
        :param config: ProgramSampler config.
        :type config: dict
        '''
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
        '''
        Generate `SynthesizerEvaluator`.
        :param syn_configs: synthesizer configs to be evaluated.
        :type syn_configs: list[dict]

        :param suffix: suffix in save path.
        :type suffix: str
        '''
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

