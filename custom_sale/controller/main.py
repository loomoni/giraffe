# from odoo import http
# from odoo.http import request
# import logging

# _logger = logging.getLogger(__name__)

import base64
import json
import logging

from odoo import http
from odoo.http import request, _logger
from odoo.tools.translate import _

logger = logging.getLogger(__name__)


class SaleOrderController(http.Controller):

    @http.route('/v1/api/create_sale_order', type='json', auth='user', methods=['POST'], csrf=False)
    def create_sale_order(self, **post):
        try:
            # Access the JSON payload of the request
            data = request.jsonrequest

            if not data:
                return http.Response("No data provided", status=400)

            # Extract transaction data
            partner_id = data.get('partner_id')
            product_lines = data.get('product_lines')

            if not partner_id or not product_lines:
                return http.Response("Missing partner_id or product_lines", status=400)

            # Create sale order
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': partner_id,
                'order_line': [(0, 0, {
                    'product_id': line['product_id'],
                    'product_uom_qty': line['quantity'],
                    'price_unit': line['price_unit'],
                }) for line in product_lines]
            })

            # Prepare response data
            sale_order_data = {
                'ID': sale_order.id,
                'lines': []
            }

            for line in sale_order.order_line:
                sale_order_data['lines'].append({
                    'ID': line.product_id.id,
                    'PRODUCT NAME': line.product_id.name,
                    'QTY': line.product_uom_qty,
                    'AMT': line.price_unit,
                    'TOTAL AMOUNT': line.price_subtotal
                })

            return {
                'status': 'success',
                'sale_order': sale_order_data
            }

        except Exception as e:
            _logger.error("Error creating sale order: %s", str(e))
            return http.Response(str(e), status=500)

    # Get all sale posted
    @http.route('/get_sale', type='json', auth='user')
    def get_sales(self):
        sale_rec = request.env['sale.order'].search([])
        sales = []
        for rec in sale_rec:
            vals = {
                'id': rec.id,
                'name': rec.partner_id.name
            }
            sales.append(vals)
        data = {'status': 200, 'response': sales, 'message': 'Success'}
        return data
