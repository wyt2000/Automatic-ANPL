import openai 
import asyncio
import logging
from typing import Callable, List, Any

from .LLMClient import LLMClient
from .. import Prompts

__all__ = ['GPTClient']

class GPTClient(LLMClient):

    async def _request_impl(self, task_name, messages, **kwargs):
        # Async create `ChatCompletion`, backoff when reach time limit
        for i in range(self.retry_times):
            try:
                responses = await openai.ChatCompletion.acreate(
                    messages = messages,
                    **kwargs
                )
                return responses
            except openai.error.InvalidRequestError as err:
                self.logger.debug(f'{task_name}: InvalidRequestError!')
                raise err
            except (openai.error.RateLimitError, openai.error.APIConnectionError) as err:
                await asyncio.sleep(self.retry_interval * (2 ** i))
        raise openai.error.RateLimitError

    @staticmethod
    def get_response_list(responses: str):
        # Convert GPT responses to list[str]
        return [response["message"]["content"] for response in responses["choices"]]

    async def request(self,
                      task_name: str,
                      task_kind: str, 
                      prompt_template: str, 
                      prompt_kwargs: dict = {},
                      prompt_background: str = Prompts.Background,
                      response_verifier: Callable[[str], bool] = lambda _ : True,
                      response_handlers: List[Callable[[str], str]] = [],
                      response_collector: Callable[[List[str]], Any] = lambda x : x,
                      response_saver: Callable[[Any], None] = lambda _ : None,
                      completion_kwargs: dict = {},
                      num_completions: int = 1,
                      retry_times: int = 1,
                      verbose: bool = True) -> Any:
        # Abstract request GPT for completions.

        # Whether output logs or not
        logger = self.logger if verbose else logging.getLogger('dummy')

        # Look up cache and load at most `num_completions` responses.
        responses = []
        prompt = prompt_template.format(**prompt_kwargs)
        cache_key = (task_name, prompt, sorted(completion_kwargs.items()))
        if (cache_value := self.cacheManager.load(task_kind, *cache_key)) is not None:
            logger.debug(f'{task_name}: [{task_kind}] cache hit!')
            responses.extend(cache_value)

        # Build up prompts.
        messages = [
            {"role": "system", "content": prompt_background},
            {"role": "user", "content": prompt}
        ]
        # Request for remaining responses, extract the results and verify them.
        for i in range(retry_times):
            if len(responses) >= num_completions:
                break
            logger.debug(f'{task_name}: [{task_kind}] requesting for {num_completions-len(responses)} responses...')
            new_responses = await self._request_impl(
                task_name        = task_name,
                messages         = messages,
                n                = num_completions - len(responses),
                **completion_kwargs
            )
            new_responses = self.get_response_list(new_responses)
            for handler in response_handlers:
                new_responses = list(map(handler, new_responses))
            responses.extend(filter(response_verifier, new_responses))
        responses = responses[:num_completions]
        logger.debug(f'{task_name}: [{task_kind}] request done!')

        # Save raw responses in cache.
        self.cacheManager.save(task_kind, responses, *cache_key)
        # Convert responses to compact format and save them in files.
        responses = response_collector(responses)
        response_saver(responses)
        return responses
