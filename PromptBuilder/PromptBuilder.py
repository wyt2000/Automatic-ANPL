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

    def clear(self):
        self.message = [
            {"role": "system", "content": self.background}
        ]

    @abstractmethod
    def build_solution_request(self, question):
        pass

    @abstractmethod
    def build_translation_request(self, solution_plan, starter_code):
        pass
    
    def get_response(self, response):
        status_code = response["choices"][0]["finish_reason"]
        assert status_code == "stop", f"The status code was {status_code}."
        response = response["choices"][0]["message"]["content"]
        self.message.append({"role": "assistant", "content": response})
        return response

