import base64
import json
import logging

from odoo import http, fields
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
            warehouse_id = data.get('warehouse_id')
            pump_no = data.get('pump_no')
            nozzle_no = data.get('nozzle_no')
            pump_reading = data.get('pump_reading')

            if not partner_id or not product_lines:
                _logger.error("Missing partner_id, product_lines, or warehouse_id in the request data.")
                return http.Response("Missing partner_id, product_lines, or warehouse_id", status=400)

            sale_order_lines = []

            # Loop through each product line to find the corresponding product in the given warehouse
            for line in product_lines:
                station_product_id = line.get('station_product_id')
                quantity = line.get('quantity')
                # warehouse_id = line.get('warehouse_id')
                price_subtotal = line.get('price_subtotal')

                if not station_product_id or not quantity or not price_subtotal:
                    _logger.error("Missing station_product_id, quantity, or price_unit in a product line.")
                    return http.Response("Missing station_product_id, quantity, or price_unit in a product line",
                                         status=400)

                # Find the product based on warehouse_code and station_product_id in product_template
                product_template = request.env['product.template'].sudo().search([
                    ('warehouse_id.code', '=', warehouse_id),
                    ('station_product_id', '=', station_product_id)
                ], limit=1)

                if not product_template:
                    error_message = f"Product with warehouse_id '{warehouse_id}' and station_product_id '{station_product_id}' not found."
                    _logger.error(error_message)
                    return {
                        'status': 'error',
                        'message': error_message
                    }

                # Find the product variant
                product = request.env['product.product'].sudo().search([
                    ('product_tmpl_id', '=', product_template.id)
                ], limit=1)

                if not product:
                    error_message = f"Product variant for template ID {product_template.id} not found."
                    _logger.error(error_message)
                    return {
                        'status': 'error',
                        'message': error_message
                    }

                # Validate stock levels for the product
                if product.qty_available < quantity:
                    error_message = f"Insufficient stock for product {product.name}. Available: {product.qty_available}, Required: {quantity}"
                    _logger.error(error_message)
                    return {
                        'status': 'error',
                        'message': error_message
                    }

                sale_order_lines.append((0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': quantity,
                    'price_subtotal': price_subtotal,
                }))

            # Create sale order
            sale_order = request.env['sale.order'].sudo().create({
                'partner_id': partner_id,
                'pump_no': pump_no,
                'nozzle_no': nozzle_no,
                'pump_reading': pump_reading,
                'order_line': sale_order_lines
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

            # Create and post the invoice
            invoice = sale_order._create_invoices()
            if invoice:
                invoice.sudo().action_post()

            # Register the payment
            # payment_vals = {
            #     'amount': invoice.amount_total,
            #     'payment_date': fields.Date.today(),
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
                    # 'AMT': line.price_unit,
                    'TOTAL AMOUNT': line.price_subtotal
                })

            return {
                'status': 'success',
                'sale_order': sale_order_data,
                'invoice_id': invoice.id if invoice else None,
                # 'payment_id': payment.id if payment else None
            }

        except Exception as e:
            _logger.error("Error creating sale order: %s", str(e), exc_info=True)
            return http.Response(str(e), status=500)
