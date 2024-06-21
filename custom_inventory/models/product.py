# models/product.py
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', store=True)
    station_product_id = fields.Char(string='Station Product ID')

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            existing_products = self.env['product.template'].search([('warehouse_id', '=', self.warehouse_id.id)])
            self.station_product_id = str(len(existing_products) + 1)

    @api.model
    def create(self, vals):
        if vals.get('warehouse_id'):
            warehouse_id = vals['warehouse_id']
            existing_products = self.env['product.template'].search([('warehouse_id', '=', warehouse_id)])
            vals['station_product_id'] = str(len(existing_products) + 1)
        return super(ProductTemplate, self).create(vals)

#  product_tmpl_id
#