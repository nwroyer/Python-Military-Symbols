import os
import sys

sys.path.append(os.path.dirname(__file__))
from command_line import *
from schema import Schema as Schema
from symbol import Symbol as Symbol
from template import Template as Template
from output_style import OutputStyle as OutputStyle

if __name__ == '__main__':
    command_line_main()




