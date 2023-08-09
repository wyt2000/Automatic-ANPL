import argparse
from anpl.parser import ANPLParser
from anpl.synthesizer import fun_synthesis
import openai
import os
from utils import read_anpl, save, clean_anpl

openai.api_key = os.environ['OPENAI_API_KEY']

class ANPLCompiler():

    def __init__(self, max_try_times=20, max_temperature=0.5):
        self.anplp = ANPLParser()
        self.max_try_times = max_try_times
        self.max_temperature = max_temperature

    def compile(self, name, code, save_path):
        anplp = self.anplp
        anpl = self.anplp.parse(code)
        holes = anpl.get_holes()
        for hole in holes:
            for i in range(self.max_try_times):
                print(f"{name}: {i}th {hole}")
                res = fun_synthesis(anpl, hole, temp=i*(self.max_temperature / self.max_try_times))
                print(f"{name}: {repr(res)}")
                newanpl = anplp.try_parse(res, from_user=False)
                if not newanpl:
                    continue
                if not hole.startswith("_hole") and hole in newanpl.funs:
                    newanpl.clean(hole)
                elif newanpl.entry in anpl.funs:
                    if not clean_anpl(anpl, newanpl):
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
    
