"""Tokenise a raw program."""
import re

from ply import lex


METHODS = [
    'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'
]

KEYWORDS = [
    'table', 'format', 'exclude', 'select', 'join', 'as', 'fk'
]

tokens = [
    'LAMBDA',
    'SEMICOLON',
    'STRING',
    'METHOD',
    'NAME',
    'PATH_SEGMENT',
    'UPDIR_SEGMENT',
    'CAPTURING_SEGMENT',
    'OPEN_BRACES',
    'CLOSE_BRACES',
    'OPEN_BRACKET',
    'CLOSE_BRACKET',
    'COLON',
    'OPEN_PAREN',
    'CLOSE_PAREN',
    'COMMA',
    'PIPE',
    'INTEGER',
    'DOUBLE',
    'BOOLEAN',
    'NULL',
    'DOLLAR_SIGN',
    'DOT'
] + [kw.upper() for kw in KEYWORDS]

t_LAMBDA = '=>'
t_SEMICOLON = ';'
t_UPDIR_SEGMENT = 'r\.\.'
t_OPEN_BRACES = r'\{'
t_CLOSE_BRACES = r'\}'
t_COLON = ':'
t_OPEN_PAREN = r'\('
t_CLOSE_PAREN = r'\)'
t_OPEN_BRACKET = r'\['
t_CLOSE_BRACKET = r'\]'
t_COMMA = ','
t_PIPE = r'\|'
t_DOLLAR_SIGN = r'\$'
t_DOT = r'\.'


def t_WHITESPACE(t):
    r'[ \t\n]+'
    t.lexer.lineno += t.value.count('\n')
    pass # discard token


def t_COMMENT_LINE(t):
    r'\/\/.*'
    pass # discard token


def t_KEYWORD_OR_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]+'
    if t.value in METHODS:
        t.type = 'METHOD'
    elif t.value in KEYWORDS:
        t.type = t.value.upper()
    else:
        t.type = 'NAME'
    return t


def t_INTEGER(t):
    r'-?[0-9]+'
    t.value = {
        'type': 'integer',
        'value': int(t.value)
    }
    return t


def t_DOUBLE(t):
    r'-?[0-9]+.[0-9]*'
    t.value = {
        'type': 'double',
        'value': float(t.value)
    }
    return t


def t_BOOLEAN(t):
    r'(true|false)'
    t.value = {
        'type': 'boolean',
        'value': t.value == 'true'
    }
    return t


def t_NULL(t):
    r'null'
    t.value = None
    return t


def t_STRING(t):
    r'"([^"\\]|(\\["\\tn]))*"'
    # remove quotes and unescape
    t.value = t.value[1:-1].replace(
        r'\\"', '"'
    ).replace(
        r'\\n', '\n'
    ).replace(
        r'\\\\', '\\'
    ).replace(
        r'\\t', '\t'
    )
    t.value = {
        'type': 'string',
        'value': t.value
    }
    return t


def percent_decode(encoded: str) -> str:
    """Decode percent encoded text."""
    return chr(int(encoded[1:], base=16))


def t_CAPTURING_SEGMENT(t):
    r'/\{([a-z_]+):([a-z_]+)\.([a-z_]+)\}'
    m = re.match(r'/\{([a-z_]+):([a-z_]+)\.([a-z_]+)\}', t.value)
    name, table, field = m.groups()
    t.value = {
        'type': 'capturing',
        'name': name,
        'table': table,
        'field': field
    }
    return t


def t_PATH_SEGMENT(t):
    r'/(([a-zA-Z0-9\-._~!$\'()+,?*:@;=%&]+)|(%[0-9a-fA-F]{2}))*'    # repl.it highlights badly, but this is valid
    # Manage percent encodings
    t.value = {
        'type': 'path',
        'value': re.sub('%[0-9a-fA-F]{2}', percent_decode, t.value)
    }
    return t


def t_error(t):
    print(f'Illegal character {t.value[0]}')
    t.lexer.skip(1)


def t_eof(t):
    t.lexer.lineno = 1;
    return None


def make_lexer():
    return lex.lex()


if __name__ == '__main__':
    lex.runmain()
