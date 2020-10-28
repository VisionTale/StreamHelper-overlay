from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FloatField, SubmitField, HiddenField, FileField, MultipleFileField, \
    RadioField, SelectField, SelectMultipleField, TextAreaField, PasswordField
from wtforms.fields.html5 import SearchField, TelField, URLField, EmailField, DateField, DateTimeField, TimeField, \
    IntegerField, DecimalField, IntegerRangeField, DecimalRangeField
from wtforms_components import ColorField
from wtforms.validators import DataRequired, ValidationError

from . import name
from webapi.libs.text import camel_case

association_table = {
    'string': StringField,
    'textarea': TextAreaField,
    'boolean': BooleanField,
    'integer': IntegerField,
    'integer_range': IntegerRangeField,
    'float': FloatField,
    'decimal': DecimalField,
    'decimal_range': DecimalRangeField,
    'color': ColorField,
    'date': DateField,
    'time': TimeField,
    'datetime': DateTimeField,
    'email': EmailField,
    'password': PasswordField,
    'telephone': TelField,
    'url': URLField,
    'search': SearchField,
    'file': FileField,
    'files': MultipleFileField,
    'radio': RadioField,
    'select': SelectField,
    'select_multiple': SelectMultipleField,
    'hidden': HiddenField,
    'submit': SubmitField
}


def create_settings_form(config) -> FlaskForm:
    """
    Creates a settings form containing the server:port and overlay_server:port option
    :return: settings form
    """
    # not outsourced to assign default field values at creation
    class SelectServerForm(FlaskForm):
        """
            Create a form for the server settings, containing the server name with its port, the overlay server with
            its port and a save button.
        """
        server = StringField(label='CasparCG Server (domain:port)', validators=[DataRequired()],
                             default=config.get(name, 'server'))
        overlay_server = StringField(label='Overlay Server URL (protocol://domain:port/path/to/overlay)',
                                     validators=[DataRequired()], default=config.get(name, 'overlay_server'))
        submit = SubmitField(label='Save')

        def validate_server(self, server):
            s, p = server.data.split(':')
            if int(p) < 0 or int(p) > 65535:
                raise ValidationError('Port is outside of possible port numbers. Ports are between 0-65535')

    return SelectServerForm()


def create_data_form(definition: list, form_identifier: str) -> FlaskForm:
    """
    Creates a form containing all the fields dynamically created from the passed values.

    Possible field types are: string, textarea, boolean, integer, integer_range, float, decimal, decimal_range, color,
    date, time, datetime, email, password, telephone, url, search, file, files, radio, select, select_multiple, hidden,
    submit

    If you want to pass kwargs, you can add pairs of values after the tuple, where the first argument is the keyword and
    the second argument the value (note that some fields like select require you to pass arguments). See
    https://wtforms.readthedocs.io/en/2.3.x/fields/ and https://wtforms-components.readthedocs.io/en/latest/
    (for ColorField).

    :param definition: definition containing of a tuple per value: (field_name: str, default_value: str,
        store_type: casting function, field_type: see above, **)
    :param form_identifier: unique identifier for the form
    :return: generated form
    """
    # Create class for the form of the overlay
    class DataForm(FlaskForm):
        pass

    setattr(DataForm, f'{form_identifier}.channel', IntegerField(label='Channel', id='channel', default=1))
    setattr(DataForm, f'{form_identifier}.layer', IntegerField(label='Layer', id='layer', default=10))

    # Iterate over all fields
    for field in definition:
        field_name = field[0]
        default_value = field[1]
        field_type = field[3]

        field_args = dict()
        field_args['label'] = camel_case(field_name, '_')
        field_args['default'] = str(default_value).rstrip()

        f = association_table.get(field_type, HiddenField)

        i = 4
        while i+1 < len(field):
            field_args[field[i]] = field[i+1]
            i += 2

        # Set the field attribute to the class (not to an object!)
        setattr(DataForm, f'{form_identifier}.{field[0]}', f(**field_args))

    # Set the rest of the buttons
    setattr(DataForm, f'{form_identifier}.play', SubmitField(label='Play', id='play'))
    setattr(DataForm, f'{form_identifier}.update', SubmitField(label='Update', id='update'))
    setattr(DataForm, f'{form_identifier}.stop', SubmitField(label='Stop', id='stop'))
    setattr(DataForm, f'{form_identifier}.delete', SubmitField(label='Delete', id='delete'))

    # Create the form for the overlay
    return DataForm()
