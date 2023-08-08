import argparse
from anpl.parser import ANPLParser
from anpl.synthesizer import fun_synthesis
import openai
import os
from utils import read_anpl, save, clean_anpl

openai.api_key = os.environ['OPENAI_API_KEY']

class ANPLCompiler():

    def __init__(self):
        self.anplp = ANPLParser()

    def compile(self, code, save_path):
        anplp = self.anplp
        anpl = self.anplp.parse(code)
        holes = anpl.get_holes()
        for hole in holes:
            for i in range(5):
                print(f"{i}th: {hole}")
                res = fun_synthesis(anpl, hole, temp=i*0.1)
                print("GPT>")
                print(res)
                newanpl = anplp.try_parse(res, from_user=False)
                if not newanpl:
                    print("SyntaxError")
                    continue
                if not hole.startswith("_hole") and hole in newanpl.funs:
                    newanpl.clean(hole)
                elif newanpl.entry in anpl.funs:
                    if not clean_anpl(anpl, newanpl):
                        print("Error: Cannot find the entry")
                        continue
                anpl.fill_fun(hole, newanpl)
                break
        if len(anpl.get_holes()) > 0:
            raise NotImplementedError("Cannot Synthesis your code")
        save(anpl, save_path)
