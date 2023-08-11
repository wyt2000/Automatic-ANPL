import openai

class GPTClient:

    def request(self, model_name, func_name, prompt, save_path, prompt_wrapper, response_wrapper):
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

        '''
        messages = prompt_wrapper.wrap(prompt, func_name)
        response = openai.ChatCompletion.create(model=model_name, messages=messages)
        status_code = response["choices"][0]["finish_reason"]
        assert status_code == "stop", f"The status code was {status_code}."
        response = response["choices"][0]["message"]["content"]
        with open(save_path, 'w') as f:
            f.write(response)
        return response_wrapper.wrap(response)

