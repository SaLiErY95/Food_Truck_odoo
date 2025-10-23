"""
Represents additional services requested by a vendor application.

Each service line corresponds to a product from the standard product
catalogue.  Services may include extra power, waste fees or rental
items.  Lines are later converted into sales order lines during
invoicing.
"""

from odoo import api, fields, models


class FoodServiceLine(models.Model):
    _name = 'food.service.line'
    _description = 'Food Festival Service Line'
    _order = 'application_id, id'

    application_id = fields.Many2one(
        'food.vendor.application',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        required=True,
        string='Service Product',
        domain=[('sale_ok', '=', True)],
    )
    qty = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Monetary(
        string='Unit Price',
        currency_field='currency_id',
        help='Unit price for this service.  Defaults to the product sale price when added.',
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        currency_field='currency_id',
        store=True,
    )
    currency_id = fields.Many2one('res.currency', related='application_id.currency_id', store=True)

    @api.onchange('product_id')
    def _onchange_product_price(self):
        """Default the unit price based on the product list price."""
        for line in self:
            if line.product_id:
                line.price_unit = line.product_id.lst_price

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = (line.qty or 0.0) * (line.price_unit or 0.0)