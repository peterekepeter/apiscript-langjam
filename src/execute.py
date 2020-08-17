from __future__ import annotations

import typing

import peewee as pw

import werkzeug
import flask

from parser import parser


FIELD_TYPES = {
    'int': (pw.IntegerField, int),
    'double': (pw.DoubleField, float),
    'varchar': (pw.CharField, str),
    'blob': (pw.BlobField, str),
    'datetime': (pw.DateTimeField, str),
    'bool': (pw.BooleanField, bool)
    # TODO: Add more field types, see
    # https://docs.peewee-orm.com/en/3.6.0/peewee/models.html#fields
}

FIELD_ARGS = {
    'pk': 'primary_key',
    'null': 'null',
    'index': 'index',
    'unique': 'unique'
    # TODO: Add more field args, see
    # https://docs.peewee-orm.com/en/3.6.0/peewee/models.html#field-initialization-arguments
}


class StatementContext:
    """A container for execution of a specific endpoint/statement."""

    def __init__(self, statement: typing.List[dict], context: Context):
        """Initialise it with code that may be called multiple times."""
        self.statement = statement
        self.context = Context
        self.operations = {
            'assignment': self.op_assignment,
            'format': self.op_format,
            'exclude': self.op_exclude,
            'join': self.op_join,
            'select': self.op_select
        }
        # FIXME: Is this thread safe? Do we need a seperate instance of this class for each call?
        self.current_value = None
        self.args = {}

    def __call__(self, **args: typing.Dict[str, pw.Model]):
        """Call the statement as a Flask callback."""
        self.args = args
        for operation in self.statement:
            self.operations[operation['type']](operation['parameters'])
        # FIXME: Do we need some final formatting/validation here?
        return self.current_value

    def op_assignment(self, params: typing.Dict[str, typing.Any]):
        """Assign a given value as the current value."""
        if params['type'] == 'variable':
            # it is a reference to a captured argument
            try:
                value = self.args[params['value']]
            except KeyError:
                raise NameError(f'Name not found: "{params["value"]}".')
        else:
            # it is a literal value
            value = params['value']
        self.current_value = value


class Context:
    "Serves as a state container for execution"
    
    def __init__(self, source: typing.Union[str, dict]):
        """Store source and parse if necessary."""
        if isinstance(source, str):
            self.source = parser.parse(source)
        else:
            self.source = source
        # table_mapping takes the following form:
        # {
        #     table_name(str): {
        #         'model': Peewee Model,
        #         'fields': {
        #             field_name(str): main_type (a data type),
        #             ...
        #         }
        #     },
        #     ...
        # }
        self.table_mapping = {}
        # TODO: Allow choice of database, see
        # https://docs.peewee-orm.com/en/3.6.0/peewee/database.html
        self.db = pw.SqliteDatabase('db.sqlite3')
        self.app = flask.Flask(__name__)

    def setup(self):
        """Build the ORM and Flask mappings."""
        self.build_tables()
        self.build_endpoints()

    def build_tables(self):
        """Set up Peewee and initialise the database."""
        for table in self.source['tables']:
            class ApiScriptTable(pw.Model):
                class Meta:
                    database = self.db
                    db_table = table['name']
            fields = {}
            for column in table['columns']:
                field, main_type = self.build_field(column['type'])
                field.add_to_class(ApiScriptTable, column['name'])
                fields[column['name']] = main_type
            self.table_mapping[table['name']] = {
                'model': ApiScriptTable,
                'fields': fields
            }
        self.db.connect()
        self.db.create_tables(self.table_mapping.values())

    def build_field(self, type_specs: typing.List[dict]) -> pw.Field:
        """Build a Peewee field."""
        class_ = None
        main_type = None
        args = {}
        for type_spec in type_specs:
            if type_spec['type'] == 'simple':
                t = type_spec['value']
                if t in FIELD_TYPES:
                    if not class_:
                        class_ = FIELD_TYPES[t][0]
                        main_type = FIELD_TYPES[t][1]
                    else:
                        raise TypeError('Multiple type specifiers used.')
                elif t in FIELD_ARGS:
                    args[FIELD_ARGS[t]] = True
                else:
                    raise TypeError(f'Invalid type specifier "{t}".')
        if class_:
            return class_(**args), main_type
        else:
            raise TypeError('Missing type specifier.')

    def build_endpoints(self):
        """Build the flask endpoints."""
        for n, endpoint in enumerate(self.source['endpoints']):
            route = self.resolve_path(endpoint['endpoint'])
            self.app.add_url_rule(
                route, str(n),
                StatementContext(endpoint['statement'], self),
                methods=[endpoint['method']]
            )

    def resolve_path(self, segments: typing.List[dict]) -> str:
        """Convert a parsed path to a Flask path."""
        path = ''
        for segment in segments:
            if segment['type'] == 'path':
                path += segment['value']
            elif segment['type'] == 'capturing':
                qualified_field = '{table}.{field}'.format(**segment)
                if qualified_field not in self.app.url_map.converters:
                    model = self.table_mapping[segment['table']]
                    main_type = model['fields'][segment['field']]
                    class ApiScriptConverter(werkzeug.routing.BaseConverter):
                        def to_python(self, value):
                            try:
                                value = main_type(value)
                            except ValueError:
                                flask.abort(404)
                            peewee_model = model['model']
                            field = getattr(peewee_model, segment['field'])
                            objects = peewee_model.select().where(field == value).objects()
                            if len(objects) == 0:
                                # FIXME: raise 404 somehow?
                                raise ValueError('No matching records.')
                            elif len(objects) == 1:
                                return objects[0]
                            else:
                                # FIXME: What to do in case of mulitple matches?
                                # Should it require captured segments to be unique fields?
                                raise ValueError('Multiple records found.')
                        def to_url(self, object):
                            return getattr(object, segment['field'])
                    self.app.url_map.converters[qualified_field] = ApiScriptConverter
                name = segment['name']
                path += f'/<{qualified_field}:{name}>'
        return path
