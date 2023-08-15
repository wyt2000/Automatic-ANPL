from ProgramSampler                         import ProgramSampler 
from Synthesizer.ANPLSynthesizer            import ANPLSynthesizer
from PromptWrapper.ANPLPromptWrapper        import ANPLPromptWrapper
from ResponseWrapper.ANPLResponseWrapper    import ANPLResponseWrapper
from Synthesizer.ParselSynthesizer          import ParselSynthesizer
from PromptWrapper.ParselPromptWrapper      import ParselPromptWrapper
from ResponseWrapper.ParselResponseWrapper  import ParselResponseWrapper
from SynthesizerEvaluator                   import SynthesizerEvaluator
from utils                                  import mkdir_override
import logging.config

if __name__ == '__main__':

    logging.config.fileConfig('logging.conf')
    for num_snippets in range(3, 4):
        sampler = ProgramSampler()
        sampler.sample(
            num_snippets=num_snippets,
            program_dir=f'programs_{num_snippets}/',
            program_prefix=f'string_manipulation_{num_snippets}',
            prompt_dir=f'prompts_{num_snippets}/',
            seed=int(f'{num_snippets}114514')
        )

        anpl_prompt_wrapper = ANPLPromptWrapper()
        anpl_response_wrapper = ANPLResponseWrapper()
        anpl_synthesizer = ANPLSynthesizer(max_try_times=5, max_temperature=0.5)
        anpl_response_dir = f'anpl_responses_{num_snippets}/'
        anpl_result_dir = f'anpl_results_{num_snippets}/'
        anpl_log_dir= f'anpl_logs_{num_snippets}/'
        anpl_judge_status_path = f'anpl_judge_status_{num_snippets}.json'

        mkdir_override(anpl_response_dir)
        mkdir_override(anpl_result_dir)
        mkdir_override(anpl_log_dir)
        anpl_evaluator = SynthesizerEvaluator(
            synthesizer=anpl_synthesizer,
            prompt_wrapper=anpl_prompt_wrapper,
            response_wrapper=anpl_response_wrapper,
            model_name='gpt-3.5-turbo-0301',
            response_dir=anpl_response_dir,
            result_dir=anpl_result_dir,
            log_dir=anpl_log_dir
        )
        anpl_evaluator.evaluate_all(sampler.dataset, anpl_judge_status_path, num_workers=4)

        parsel_prompt_wrapper = ParselPromptWrapper()
        parsel_response_wrapper = ParselResponseWrapper()
        parsel_synthesizer = ParselSynthesizer()
        parsel_response_dir = f'parsel_responses_{num_snippets}/'
        parsel_result_dir = f'parsel_results_{num_snippets}/'
        parsel_log_dir = f'parsel_logs_{num_snippets}/'
        parsel_judge_status_path = f'parsel_judge_status_{num_snippets}.json'

        mkdir_override(parsel_response_dir)
        mkdir_override(parsel_result_dir)
        mkdir_override(parsel_log_dir)
        parsel_evaluator = SynthesizerEvaluator(
            synthesizer=parsel_synthesizer,
            prompt_wrapper=parsel_prompt_wrapper,
            response_wrapper=parsel_response_wrapper,
            model_name='gpt-3.5-turbo-0301',
            response_dir=parsel_response_dir,
            result_dir=parsel_result_dir,
            log_dir=parsel_log_dir
        )
        parsel_evaluator.evaluate_all(sampler.dataset, parsel_judge_status_path, num_workers=4)


