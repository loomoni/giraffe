import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
import json

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_price_subtotal = fields.Float(string='Custom Price Subtotal', compute='_compute_custom_price_subtotal',
                                         store=True)

    @api.depends('price_unit', 'product_uom_qty', 'discount')
    def _compute_custom_price_subtotal(self):
        for line in self:
            if line.custom_price_subtotal:
                line.price_subtotal = line.custom_price_subtotal
            else:
                line.price_subtotal = line.price_unit * line.product_uom_qty * (1 - line.discount / 100.0)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    serial_number = fields.Char(string='Serial Number')
    # sale_date = fields.Date(string='Sale Date', default=fields.Date.today)
    sale_date = fields.Date.today()
    serial_number_receipt_number = fields.Char(string='Reference', required=True)
    # Formatting the date
    formatted_sale_date = sale_date.strftime('%Y-%m-%d')

    @api.depends('order_line.price_subtotal')
    def _compute_amount_total(self):
        for order in self:
            total = sum(line.price_subtotal for line in order.order_line)
            order.amount_total = total

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount_total',
                                   track_visibility='always')

    def get_radix_token(self):
        # getway details
        gateway = self.env['psms.gateway'].search([('id', '=', 1)])
        headers = {
            'Content-Type': 'application/json',
        }
        user_login = {
            "email": gateway.username,
            "password": gateway.password
        }
        data = json.dumps(user_login)
        response = requests.post(gateway.login_url, headers=headers, data=data)
        jsonData = response.json()
        jsonData = json.dumps(jsonData)
        jsonData = json.loads(str(jsonData))
        token = jsonData['data']['token']

        return token

    def get_radix_sales(self, sale_date=formatted_sale_date):
        print("we are here")
        gateway = self.env['psms.gateway'].search([('id', '=', 1)])
        token = self.get_radix_token()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {token}"
        }
        stations = self.env['psms.station'].search([])
        for station in stations:
            try:
                sales_request = {
                    "serial_number": station.serial_number,
                    # "date": sale_date
                    "date": '2024-05-26'
                }
                print(sales_request)
                data = json.dumps(sales_request)
                response = requests.get(gateway.sales_url, headers=headers, data=data)
                jsonData = response.json()
                jsonData = json.dumps(jsonData)
                jsonData = json.loads(str(jsonData))
                print(jsonData)

                if jsonData['data']:
                    sales_data = jsonData['data']

                    for sales in sales_data:
                        # checks if reference exists
                        sale_order_lines = []
                        reference = sales['FDC_NAME'] + sales['EFD_SAVE_NUM']
                        reference_exist = self.env['sale.order'].search(
                            [('serial_number_receipt_number', '=', reference)])
                        if not reference_exist:
                            if sales['FDC_PROD_NAME'] == 'UNLEADED':
                                product_id = 1
                            elif sales['FDC_PROD_NAME'] == 'DIESEL':
                                product_id = 2
                            sale_order_lines.append((0, 0, {
                                'product_id': product_id,
                                'product_uom_qty': sales['VOL'],
                                'price_unit': sales['PRICE'],
                                'custom_price_subtotal': sales['AMO'],  # Setting custom price subtotal
                            }))
                            sale_order = self.env['sale.order'].sudo().create({
                                'partner_id': 7,
                                'date_order': sales['RDG_DATE'],
                                'serial_number_receipt_number': reference,
                                'order_line': sale_order_lines,
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
                                invoice.sudo().write({
                                    'amount_total': sale_order.amount_total,
                                    'amount_residual': sale_order.amount_total,
                                })

                                for line in invoice.invoice_line_ids:
                                    line.sudo().write({
                                        'price_subtotal': sale_order.amount_total,
                                    })

                                invoice.sudo().action_post()

                                # Open the payment registration wizard
                                payment_wizard = self.env['account.payment.register'].with_context(
                                    active_model='account.move',
                                    active_ids=invoice.ids
                                ).create({
                                    'payment_date': fields.Date.today(),
                                    'journal_id': self.env['account.journal'].search([('type', '=', 'cash')],
                                                                                     limit=1).id,
                                    'amount': sale_order.amount_total,
                                    'currency_id': invoice.currency_id.id,
                                    # 'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                })
                                # Confirm the payment in the wizard
                                payment_wizard.action_create_payments()

            except Exception as e:
                print(e)
                pass