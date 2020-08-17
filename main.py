import json
import os

from src.parser import parser
from src.tokeniser import make_lexer

lexer = make_lexer()

def run_file(file_path):
    with open(file_path) as f:
        source = f.read()

    if source.startswith('//!print_tokens'):
        lexer.input(source)
        for token in lexer:
            print(f'{token.lineno} {token.type}: {token.value!r}')
            
    result = parser.parse(source, lexer)
    print(json.dumps(result, indent=4))


def run_all(dir):
    files = os.listdir(dir)
    case_separator = ''
    for file in files:
        file_path = f'{dir}/{file}'
        print(f'{case_separator}{file_path}:\n')
        run_file(file_path)
        case_separator = '\n\n'


run_all('examples')
