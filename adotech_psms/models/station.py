from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import requests
import json


class Station(models.Model):
    '''Defining a station model.'''

    _name = 'psms.station'
    _description = 'Station'

    name = fields.Char(string='Name', required=True)
    serial_number = fields.Char(string='Serial number', required=True)
    location = fields.Char(string='Location', required=True)



















