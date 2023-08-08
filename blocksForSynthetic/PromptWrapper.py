import pathlib

class PromptWrapper:
    def __init__(self, prompt_dir='prompts/'):
        self.prompt_dir = prompt_dir
        prompts = {} 
        paths = list(pathlib.Path(prompt_dir).glob('*.prompt'))
        for path in paths:
            with open(path, 'r') as f:
                name = pathlib.Path(path).stem
                prompts[name] = f.read()
        self.prompts = prompts

    def wrap(self, pre_prompt='', post_prompt=''):
        return {name : '\n'.join([pre_prompt, prompt, post_prompt]) for name, prompt in self.prompts.items()}

if __name__ == '__main__':
    promptWrapper = PromptWrapper()
    prompts = promptWrapper.wrap('pre', 'post')
    for prompt in prompts.items():
        print(prompt)
