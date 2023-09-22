import os
import traceback
from .ANPL.anpl.parser import ANPLParser
from .Synthesizer import AbstractSynthesizer

def verify_code(anpl_code):
    anpl_parser = ANPLParser()
    anpl = anpl_parser.try_parse(anpl_code, from_user=False)
    if not anpl:
        raise Exception("Compile Error!")

