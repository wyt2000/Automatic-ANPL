import openai
import logging 
import aiohttp

class GPTClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def request(self, model_name, func_name, prompt, save_path, prompt_wrapper, response_wrapper):
        '''
        Request to ChatGPT for Synthesizer's DSL.
        Ensure that the environment variable OPENAI_API_KEY is set correctly.
        
        :param model_name: GPT model name, eg: GPT-4
        :type model_name: str

        :param func_name: May be used in wrapper.
        :type func_name: str

        :param prompt: Raw prompts from program sampler.
        :type prompt: str

        :param save_path: The path to save raw responses from ChatGPT.
        :type save_path: str

        :param prompt_wrapper: Convert raw prompts to synthesizer specific prompts.
        :type prompt_wrapper: PromptWrapper 

        :param response_wrapper: Extract DSL from raw response.
        :type response_wrapper: ResponseWrapper

        :return: The input DSL of synthesizer.
        :rtype: str

        '''
        messages = prompt_wrapper.wrap(prompt, func_name)
        self.logger.debug(f"Sending prompt:\n{prompt}")
        # ref: https://github.com/openai/openai-python/issues/278#issuecomment-1473357978
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            response = await openai.ChatCompletion.acreate(model=model_name, messages=messages)
        self.logger.debug(f"Received response:\n{response}")
        status_code = response["choices"][0]["finish_reason"]
        assert status_code == "stop", f"The status code was {status_code}."
        response = response["choices"][0]["message"]["content"]
        with open(save_path, 'w') as f:
            f.write(response)
        return response_wrapper.wrap(response)

