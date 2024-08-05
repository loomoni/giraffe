from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import requests
import json


class Gateway(models.Model):
    '''Defining a gateway model.'''

    _name = 'psms.gateway'
    _description = 'Gateway'

    name = fields.Char(string='Name', required=True)
    login_url = fields.Char(string='Login Url', required=True)
    sales_url = fields.Char(string='Sales Url', required=True)
    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Password', required=True)



















