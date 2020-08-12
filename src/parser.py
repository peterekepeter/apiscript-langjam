"""Parse a tokenised program."""
import json

from ply import yacc

from .tokeniser import tokens


def p_program(p):
    """program : empty"""
    p[0] = {
        'tables': (),
        'endpoints': ()
    }


def p_program_endpoint(p):
    """program : endpoint_definition program"""
    p[0] = {
        'tables': p[2]['tables'],
        'endpoints': [p[1], *p[2]['endpoints']]
    }


def p_program_table(p):
    """program : table_definition program"""
    p[0] = {
        'tables': [p[1], *p[2]['tables']],
        'endpoints': p[2]['endpoints']
    }


def p_table_definition(p):
    """table_definition : TABLE NAME OPEN_BRACES table_columns CLOSE_BRACES"""
    p[0] = p[4]


def p_table_columns(p):
    """table_columns : table_column table_columns_not_whitespace
                     | empty
    """
    if len(p) == 3:
        p[0] = (p[1], *p[2])
    else:
        p[0] = ()


def p_table_columns_not_whitespace(p):
    """table_columns_not_whitespace : table_column table_columns_not_whitespace
                                    | empty
    """
    if len(p) == 3:
        p[0] = (p[1], *p[2])
    else:
        p[0] = ()


def p_table_column(p):
    """table_column : NAME COLON table_column_type opt_table_column_types SEMICOLON"""
    p[0] = {
        'name': p[1],
        'type': (p[3], *p[4])
    }


def p_opt_table_column_types(p):
    """opt_table_column_types : table_column_types
                              | empty
    """
    if p[1]:
        p[0] = p[1]
    else:
        p[0] = ()


def p_table_column_types(p):
    """table_column_types : table_column_type table_column_types
                          | table_column_type
    """
    if len(p) == 3:
        p[0] = (p[1], *p[2])
    else:
        if p[1]:
            p[0] = (p[1],)
        else:
            p[0] = ()


def p_table_column_type(p):
    """table_column_type : NAME
                         | FK OPEN_PAREN NAME DOT NAME AS NAME CLOSE_PAREN
    """
    if len(p) == 2:
        p[0] = {
            'type': 'simple',
            'value': p[1]
        }
    else:
        p[0] = {
            'type': 'foreign_key',
            'table': p[3],
            'field': p[5],
            'backref': p[7]
        }


def p_endpoint_definition(p):
    """endpoint_definition : METHOD endpoint LAMBDA statement SEMICOLON"""
    p[0] = {
        'method': p[1],
        'endpoint': p[2],
        'statement': p[4]
    }


def p_endpoint(p):
    """endpoint : DOT endpoint_not_start
                | UPDIR_SEGMENT endpoint_not_start
                | endpoint_not_start
    """
    if len(p) == 3:
        p[0] = (p[1], *p[2])
    else:
        p[0] = p[1]


def p_endpoint_not_start(p):
    """endpoint_not_start : PATH_SEGMENT opt_endpoint
                          | CAPTURING_SEGMENT opt_endpoint
    """
    p[0] = (p[1], *p[2])


def p_opt_endpoint(p):
    """opt_endpoint : endpoint
                    | empty
    """
    if p[1]:
        p[0] = p[1]
    else:
        p[0] = ()


def p_statement(p):
    """statement : command commands"""
    p[0] = (p[1], *p[2])


def p_commands(p):
    """commands : PIPE command commands
                | empty
    """
    if len(p) == 4:
        p[0] = (p[2], *p[3])
    else:
        p[0] = ()


def p_command_raw(p):
    """command : raw_value"""
    p[0] = {
        'type': 'assignment',
        'value': p[1]
    }


def p_command_variable(p):
    """command : DOLLAR_SIGN NAME"""
    p[0] = {
        'type': 'assignment',
        'parameters': {
            'type': 'variable',
            'value': p[2]
        }
    }


def p_command_keyword(p):
    """command : FORMAT NAME
               | EXCLUDE compound_name_list
               | JOIN db_query
               | SELECT db_query
    """
    p[0] = {
        'type': p[1],
        'parameters': p[2]
    }


def p_compound_name_list(p):
    """compound_name_list : compound_name compound_name_list_not_start
                          | empty
    """
    if len(p) == 3:
        p[0] = (p[1], *p[2])
    else:
        p[0] = ()


def p_compound_name_list_not_start(p):
    """compound_name_list_not_start : COMMA compound_name compound_name_list_not_start
                                    | empty
    """
    if len(p) == 4:
        p[0] = (p[2], *p[3])
    else:
        p[0] = ()


def p_compound_name(p):
    """compound_name : NAME DOT compound_name
                     | NAME
    """
    if len(p) == 3:
        p[0] = (p[1], *p[3])
    else:
        p[0] = ()


def p_db_query_list(p):
    """db_query_list : db_query_item COMMA db_query_list
                     | empty
    """
    if len(p) == 4:
        p[0] = (p[1], *p[3])
    else:
        p[0] = ()


def p_db_query_item(p):
    """db_query_item : db_query
                     | NAME
    """
    if isinstance(p[1], str):
        p[0] = {
            'type': 'field',
            'name': p[1]
        }
    else:
        p[0] = p[1]


def p_db_query(p):
    """db_query : compound_name OPEN_PAREN db_query_list CLOSE_PAREN"""
    p[0] = {
        'type': 'join_or_select',
        'key_or_table': p[1],
        'fields': p[3]
    }


def p_raw_value(p):
    """raw_value : STRING
                 | INTEGER
                 | DOUBLE
                 | BOOLEAN
                 | NULL
                 | list
                 | object
    """
    p[0] = p[1]


def p_list(p):
    """list : OPEN_BRACKET list_elements CLOSE_BRACKET"""
    p[0] = {
        'type': 'list',
        'value': p[2]
    }


def p_list_element(p):
    """list_elements : raw_value COMMA list_elements
                     | empty
    """
    if len(p) == 4:
        p[0] = (p[1], *p[3])
    else:
        p[0] = ()


def p_object(p):
    """object : OPEN_BRACES object_elements CLOSE_BRACES"""
    p[0] = {
        'type': 'object',
        'value': p[2]
    }


def p_object_elements(p):
    """object_elements : STRING COLON raw_value COMMA object_elements
                       | empty
    """
    if len(p) == 6:
        prev = p[5]
        prev[p[1]] = p[3]
        p[0] = prev
    else:
        p[0] = {}


def p_empty(p):
    """empty : """
    p[0] = None


def p_error(t):
    if t:
        lines = t.lexer.lexdata.split('\n')
        before = sum(len(line) + 1 for line in lines[:t.lineno - 1])
        col = t.lexpos - before
        print(f'Syntax error near {t.value!r} ({t.type}), line {t.lineno}:{col}.')
    else:
        print('Unexpected EOF.')


parser = yacc.yacc()


if __name__ == '__main__':
    while True:
        try:
            s = input('> ')
        except EOFError:
            break
        if not s: continue
        result = parser.parse(s)
        print(json.dumps(result, indent=4))
