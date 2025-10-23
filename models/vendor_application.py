"""
Core model to manage vendor applications for food truck festivals.

Applications are created from a public website form or manually by
staff.  They store the company's details, requested services, booth
preferences and workflow state.  When an application is approved
the system automatically assigns a booth, generates a contract for
e‑signature, and creates a sale order and invoice upon signature.
"""

import secrets
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FoodVendorApplication(models.Model):
    _name = 'food.vendor.application'
    _description = 'Food Festival Vendor Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # sequence field
    name = fields.Char(
        string='Application Number',
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('food.vendor.application') or _('New'),
        copy=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Company',
        domain="['|',('company_type','=','company'),('company_type','=',False)]",
        tracking=True,
    )
    company_name_fallback = fields.Char(string='Company Name')
    vat_fallback = fields.Char(string='VAT')
    phone_fallback = fields.Char(string='Phone')
    email_fallback = fields.Char(string='Email')

    menu_description = fields.Html(string='Menu Description', translate=True)
    allergen_category_ids = fields.Many2many('res.partner.category', string='Allergens')
    truck_width = fields.Float(string='Truck Width (m)')
    truck_depth = fields.Float(string='Truck Depth (m)')
    needs_power_kw = fields.Float(string='Power Required (kW)', help='Power consumption requested by the vendor.')
    needs_water = fields.Boolean(string='Needs Water')
    needs_sewage = fields.Boolean(string='Needs Sewage')

    event_id = fields.Many2one('event.event', string='Event', required=True, tracking=True)
    day_ids = fields.Many2many('food.event.day', string='Days')
    booth_id = fields.Many2one('food.booth', string='Assigned Booth')
    service_line_ids = fields.One2many('food.service.line', 'application_id', string='Service Lines')

    pricing_package = fields.Selection([
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ], string='Pricing Package', default='basic')
    computed_subtotal = fields.Monetary(string='Subtotal', compute='_compute_totals', store=True)
    taxes = fields.Monetary(string='Taxes', compute='_compute_totals', store=True)
    computed_total = fields.Monetary(string='Total', compute='_compute_totals', store=True)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True)

    state = fields.Selection([
        ('new', 'New'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('contract_sent', 'Contract Sent'),
        ('signed', 'Signed'),
        ('invoiced', 'Invoiced'),
        ('checked_in', 'Checked‑In'),
        ('closed', 'Closed'),
    ], default='new', tracking=True)

    sign_request_id = fields.Many2one('sign.request', string='Sign Request')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    portal_token = fields.Char(string='Portal Token', copy=False)
    checkin_time = fields.Datetime(string='Check‑In Time')

    # related fields
    booth_power_kw = fields.Float(related='booth_id.power_kw', string='Booth Power', readonly=True)
    currency_rate = fields.Float(related='currency_id.rate')

    # attachments (licenses etc.) can be stored in chatter; we leave as attachments

    @api.depends('event_id')
    def _compute_currency(self):
        for app in self:
            if app.event_id:
                app.currency_id = app.event_id.company_id.currency_id
            else:
                app.currency_id = self.env.company.currency_id

    @api.depends('booth_id', 'service_line_ids.subtotal', 'day_ids')
    def _compute_totals(self):
        for app in self:
            subtotal = 0.0
            # price for booth per day
            if app.booth_id:
                days_count = len(app.day_ids) or 1
                subtotal += (app.booth_id.price_per_day or 0.0) * days_count
            # service lines
            subtotal += sum(app.service_line_ids.mapped('subtotal'))
            app.computed_subtotal = subtotal
            # compute taxes using company's tax; simple 0 for placeholder
            tax = 0.0
            app.taxes = tax
            app.computed_total = subtotal + tax

    def _ensure_partner(self):
        """Create or update partner if not already set."""
        for app in self:
            if not app.partner_id:
                vals = {
                    'name': app.company_name_fallback or 'New Vendor',
                    'vat': app.vat_fallback,
                    'phone': app.phone_fallback,
                    'email': app.email_fallback,
                    'company_type': 'company',
                    'customer_rank': 1,
                }
                partner = self.env['res.partner'].create(vals)
                app.partner_id = partner.id
            return app.partner_id

    def _check_documents(self):
        """Placeholder for required document validation.  Should be
        extended via inheritance or overrides to verify required
        attachments exist.  Raises UserError if validation fails."""
        # Example: check if there are attachments in chatter
        for app in self:
            # In a real implementation, you would check compliance lines or attachments
            pass

    # Workflow actions
    def action_submit(self):
        for app in self:
            app._ensure_partner()
            app.state = 'review'
        return True

    def action_approve(self):
        for app in self:
            # ensure documents
            app._check_documents()
            # assign booth if not set
            if not app.booth_id:
                booth = app._find_available_booth()
                if not booth:
                    raise UserError(_('No suitable booth available.'))
                booth.write({'state': 'reserved', 'application_id': app.id})
                app.booth_id = booth
            # check requested power vs booth
            if app.needs_power_kw and app.booth_id and app.needs_power_kw > app.booth_id.power_kw:
                raise ValidationError(_('Requested power exceeds booth capability.'))
            app.state = 'approved'
            # generate portal token if missing
            if not app.portal_token:
                app.portal_token = secrets.token_urlsafe(16)
        return True

    def _find_available_booth(self):
        """Find an available booth matching the requirements (size, utilities)."""
        self.ensure_one()
        domain = [
            ('event_id', '=', self.event_id.id),
            ('state', '=', 'available'),
        ]
        if self.needs_water:
            domain.append(('water', '=', True))
        if self.needs_sewage:
            domain.append(('sewage', '=', True))
        if self.needs_power_kw:
            domain.append(('power_kw', '>=', self.needs_power_kw))
        # optionally filter by size
        booth = self.env['food.booth'].search(domain, limit=1)
        return booth

    def action_reject(self):
        for app in self:
            app.state = 'rejected'
        return True

    def action_send_contract(self):
        """Create a sign request from a predefined template and send to vendor."""
        template = self.env.ref('food_truck_festival.sign_template_vendor_contract', raise_if_not_found=False)
        for app in self:
            if not template:
                raise UserError(_('Sign template not configured.'))
            # ensure partner exists
            partner = app._ensure_partner()
            # prepare sign request
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'signer_ids': [(0, 0, {
                    'partner_id': partner.id,
                    'role_id': template.signer_ids and template.signer_ids[0].role_id.id or False,
                })],
                'reference': app.name,
            })
            app.sign_request_id = sign_request
            app.state = 'contract_sent'
            # Send the request
            sign_request.action_sent()
            # Post a message to the chatter
            app.message_post(body=_('Contract sent for e‑signature.'))
        return True

    def action_mark_signed(self):
        """Called when the contract is signed.  Create a sale order and invoice."""
        for app in self:
            if app.state not in ('contract_sent', 'approved'):
                continue
            app.state = 'signed'
            # create sale order
            order = app._create_sale_order()
            app.sale_order_id = order
            # create invoice
            invoice = app._create_invoice(order)
            app.invoice_id = invoice
            app.state = 'invoiced'
            app.message_post(body=_('Contract signed. Sales order and invoice generated.'))
        return True

    def _create_sale_order(self):
        self.ensure_one()
        order_vals = {
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'state': 'draft',
            'order_line': [],
        }
        # Booth line
        if self.booth_id:
            product = self.env['product.product'].create({
                'name': _('Festival Booth %s') % self.booth_id.name,
                'type': 'service',
                'lst_price': self.booth_id.price_per_day,
                'sale_ok': True,
            })
            order_vals['order_line'].append((0, 0, {
                'product_id': product.id,
                'product_uom_qty': len(self.day_ids) or 1,
                'price_unit': self.booth_id.price_per_day,
            }))
        # Service lines
        for line in self.service_line_ids:
            order_vals['order_line'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'price_unit': line.price_unit,
            }))
        order = self.env['sale.order'].create(order_vals)
        # confirm order to generate deliveries/invoice triggers; we leave in draft for manager to confirm
        return order

    def _create_invoice(self, order):
        """Create a draft invoice from the sale order."""
        invoice_vals = order._prepare_invoice()
        invoice = self.env['account.move'].create(invoice_vals)
        # Add invoice lines from order
        invoice_line_vals = []
        for line in order.order_line:
            invoice_line_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, [])],
            }))
        invoice.write({'invoice_line_ids': invoice_line_vals})
        return invoice

    def action_check_in(self):
        for app in self:
            app.checkin_time = fields.Datetime.now()
            app.state = 'checked_in'
            app.message_post(body=_('Vendor checked in at %s') % app.checkin_time)
        return True

    # QR code / token logic
    def get_checkin_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not self.portal_token:
            self.portal_token = secrets.token_urlsafe(16)
        return f"{base_url}/food/checkin/{self.portal_token}"
