from odoo import models, fields, api

import json
import requests


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    # Additional fields can be added here if needed
    pump_no = fields.Integer(string="Pump No", store=True, readonly=True)
    nozzle_no = fields.Integer(string="Nozzle No", store=True, readonly=True)
    pump_reading = fields.Float(string="Pump reading", store=True, readonly=True)


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    price_subtotal = fields.Float(string="Price Subtotal", store=True)
    manual_price_subtotal = fields.Boolean(string="Manual Price Subtotal", default=False)

    @api.model
    def create(self, vals):
        if 'price_subtotal' in vals:
            vals['manual_price_subtotal'] = True
        else:
            vals['manual_price_subtotal'] = False
            vals['price_subtotal'] = vals.get('product_uom_qty', 0.0) * vals.get('price_unit', 0.0)
        return super(SaleOrderLineInherit, self).create(vals)

    def write(self, vals):
        if 'price_subtotal' in vals:
            vals['manual_price_subtotal'] = True
        else:
            for record in self:
                if not record.manual_price_subtotal:
                    vals['price_subtotal'] = vals.get('product_uom_qty', record.product_uom_qty) * vals.get(
                        'price_unit', record.price_unit)
                    vals['manual_price_subtotal'] = False
        return super(SaleOrderLineInherit, self).write(vals)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            if not line.manual_price_subtotal:
                line.price_subtotal = line.product_uom_qty * line.price_unit
            taxes = line.tax_id.compute_all(line.price_subtotal, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
            })
