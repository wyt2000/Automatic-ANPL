import logging
import logging.config
import json
import dataclasses

from ConfigManager import ConfigManager

logging.config.fileConfig('logging.conf')

if __name__ == '__main__':

    logger = logging.getLogger('main')
    logger.info('Loading config...')
    configManager = ConfigManager()
    logger.info('Loading config done!')

    # For each task
    for config in configManager.config:
        # For each num_snippet
        for dataset in configManager.build_program_datasets(config['ProgramSamplerConfig']):
            num_snippets = dataset[0].num_snippets
            # For each synthesizer
            for evaluator in configManager.build_evaluators(config['SynthesizerConfig'], suffix=num_snippets):
                judge_status_path = f'{evaluator.synthesizer.name}_judge_status_{num_snippets}.json'
                try:
                    evaluator.evaluate_all(dataset)
                finally:
                    with open(judge_status_path, 'w') as f:
                        f.write(json.dumps(dataclasses.asdict(evaluator.judge_system.judge_status_container)))

