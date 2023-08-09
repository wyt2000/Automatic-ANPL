from anpl.parser import ANPLParser
from anpl.synthesizer import fun_synthesis
import openai
import os

openai.api_key = os.environ['OPENAI_API_KEY']

def clean_gpt(prev_anpl, new_anpl):
    new_fun_names = set(new_anpl.funs.keys() - prev_anpl.funs.keys())
    subfuns = set()
    for name in new_fun_names:
        if name in new_anpl.funs:
            for n in new_anpl.funs[name].dependencies:
                subfuns.add(n)
    entries = new_fun_names - subfuns
    if len(entries) == 1:
        new_anpl.clean(entries.pop())
        return True
    else:
        return False

class ANPLCompiler():
    name = 'anpl'
    def __init__(self, max_try_times=5, max_temperature=0.5):
        self.anplp = ANPLParser()
        self.max_try_times = max_try_times
        self.max_temperature = max_temperature

    def compile(self, name, code, save_path):
        anpl_parser = ANPLParser()
        anpl = anpl_parser.try_parse(code)
        holes = anpl.get_holes()
        for hole in holes:
            for i in range(5):
                print(f"{name}: {i}th {hole}")
                res = fun_synthesis(anpl, hole, temp=i*0.1)
                print(f"{name}: {repr(res)}")
                if res:
                    newanpl = anpl_parser.try_parse(res, from_user=False)
                    if newanpl:
                        if not hole.startswith("_hole"):
                            if hole in newanpl.funs:
                                newanpl.clean(hole)
                            else:
                                continue
                        else:
                            if newanpl.entry in anpl.funs:
                                is_one_fun = clean_gpt(anpl, newanpl)
                                if not is_one_fun:
                                    continue
                        anpl.fill_fun(hole, newanpl)
                        break

        if len(anpl.get_holes()) > 0:
            print(f"{name}: ANPL Synthesis Failed!")
            return None
        print(f"{name}: ANPL Synthesis Success!")
        code = anpl.to_python()
        with open(save_path, "w") as f:
            f.write(code)
        return code
    
