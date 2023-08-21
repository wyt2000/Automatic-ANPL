from abc import ABC, abstractmethod 

class AbstractPromptBuilder(ABC):
    '''
    Abstract base class of `PromptWrapper`.
    Transform program descriptions to the prompts for ChatGPT according to specific promgram synthesizer.
    '''

    @property
    @abstractmethod
    def background(self):
        pass

    @abstractmethod
    def build_solution_request(self, question, messages):
        pass

    @abstractmethod
    def build_translation_request(self, solution_plan, starter_code, messages):
        pass

    def build_background(self):
        return [{"role": "system", "content": self.background}]

    def get_response(self, response, messages):
        status_code = response["choices"][0]["finish_reason"]
        assert status_code == "stop", f"The status code was {status_code}."
        response = response["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": response})
        return response

    @abstractmethod
    def extract_code(self, code: str):
        pass


