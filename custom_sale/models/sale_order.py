from odoo import models, fields
import json
import requests


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    # Additional fields can be added here if needed

