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
                _logger.error("No data provided in the request.")
                return http.Response("No data provided", status=400)

            # Extract transaction data
            partner_id = data.get('partner_id')
            product_lines = data.get('product_lines')

            if not partner_id or not product_lines:
                _logger.error("Missing partner_id or product_lines in the request data.")
                return http.Response("Missing partner_id or product_lines", status=400)

            # Validate stock levels for each product line
            for line in product_lines:
                product = request.env['product.product'].sudo().browse(line['product_id'])
                if product.qty_available < line['quantity']:
                    error_message = f"Insufficient stock for product {product.name}. Available: {product.qty_available}, Required: {line['quantity']}"
                    _logger.error(error_message)
                    return {
                        'status': 'error',
                        'message': error_message
                    }

            # Create sale order
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': partner_id,
                'order_line': [(0, 0, {
                    'product_id': line['product_id'],
                    'product_uom_qty': line['quantity'],
                    'price_unit': line['price_unit'],
                }) for line in product_lines]
            })

            # Confirm the sale order
            sale_order.action_confirm()

            # Validate the stock picking (delivery order)
            picking = sale_order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            if picking:
                picking.sudo().action_assign()  # Ensure picking is ready to be validated

                # Process each move line to ensure the demand and delivered quantities match
                for move_line in picking.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

                # Validate the picking
                picking.sudo().button_validate()

            # Create invoice
            invoice = sale_order._create_invoices()
            if invoice:
                invoice.sudo().action_post()

                # payment = invoice.sudo().action_register_payment()
                # if payment:
                #     payment.sudo().action_create_payments()

            # Register the payment
            # payment_vals = {
            #     'amount': invoice.amount_total,
            #     'payment_date': invoice.Date.today(),
            #     'payment_type': 'inbound',
            #     'partner_id': partner_id,
            #     'partner_type': 'customer',
            #     'journal_id': request.env['account.journal'].sudo().search([('type', '=', 'bank')], limit=1).id,
            #     'payment_method_id': request.env.ref('account.account_payment_method_manual_in').id,
            #     'invoice_ids': [(6, 0, [invoice.id])],
            # }
            # payment = request.env['account.payment'].sudo().create(payment_vals)
            # payment.sudo().post()

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
            _logger.error("Error creating sale order: %s", str(e), exc_info=True)
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
