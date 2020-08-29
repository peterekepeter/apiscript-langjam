import json
import os

from src.parser import parser
from src.tokeniser import make_lexer

lexer = make_lexer()

def test_parse_file(file_path):
    print(f'PARSE {file_path}')
    with open(file_path) as f:
        source = f.read()

    if source.startswith('//!print_tokens'):
        lexer.input(source)
        for token in lexer:
            print(f'{token.lineno} {token.type}: {token.value!r}')
            
    result = parser.parse(source, lexer)

    if source.startswith('//!print_parsed'):
        print(json.dumps(result, indent=4))


def test_parse_all(dir):
    files = os.listdir(dir)
    for file in files:
        file_path = f'{dir}/{file}'
        test_parse_file(file_path)


def exec_file(file_path, host, port):
    with open(file_path) as f:
        source = f.read()

    from src.execute import Context
    ctx = Context(source)
    ctx.setup();
    ctx.run(host, port);
        
def start_api_subprocess(file_path):
    from multiprocessing import Process
    p = Process(target = exec_file, args=(file_path, '127.0.0.1', 5000))
    p.start();
    import time
    time.sleep(1) # not the best solution but it makes sure API did initialize
    return p

def test_parse_all_examples():
    # parsing all examples makes sure we don't break the parser
    test_parse_all('examples')
    print("\n")

def test_hello_word():
    # test actually running the APIscript below
    api = start_api_subprocess('examples/hello_world.api');

    import urllib.request
    contents = urllib.request.urlopen("http://127.0.0.1:5000/").read()
    print(f'Response from API: "{contents.decode("utf-8")}"')

    api.terminate()

def test_all():
    test_parse_all_examples();
    test_hello_word();
    print('\n-- test all finish --\n')

test_all();
exec_file('examples/minisite.api', '0.0.0.0', 8080);
