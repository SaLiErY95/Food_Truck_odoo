"""
Define the booth model used to reserve physical stand locations at
events.  Each booth belongs to an event and can be reserved by
applications.  Coordinates allow the booth to be placed on a map.
"""

from odoo import api, fields, models
from odoo.tools import float_round


class FoodBooth(models.Model):
    _name = 'food.booth'
    _description = 'Food Festival Booth'
    _order = 'event_id, code'

    name = fields.Char(required=True, translate=True)
    event_id = fields.Many2one(
        'event.event',
        required=True,
        string='Event',
        ondelete='cascade',
    )
    code = fields.Char(
        string='Booth Code',
        required=True,
        help='Unique code identifying the booth within the event.',
    )
    width_m = fields.Float(string='Width (m)', default=3.0)
    depth_m = fields.Float(string='Depth (m)', default=3.0)
    area_sqm = fields.Float(string='Area (sqm)', compute='_compute_area', store=True)
    power_kw = fields.Float(string='Power (kW)', help='Maximum power available for the booth.', default=2.0)
    water = fields.Boolean(string='Water Hook‑Up')
    sewage = fields.Boolean(string='Sewage Hook‑Up')
    price_per_day = fields.Monetary(string='Daily Price', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='event_id.company_id.currency_id', store=True)
    x_coord = fields.Float(string='X Coordinate', help='X coordinate on the map (percentage of image width).')
    y_coord = fields.Float(string='Y Coordinate', help='Y coordinate on the map (percentage of image height).')
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
    ], default='available', string='State')
    application_id = fields.Many2one('food.vendor.application', string='Vendor Application')

    _sql_constraints = [
        (
            'unique_event_code',
            'unique(event_id, code)',
            'The booth code must be unique per event.',
        ),
    ]

    @api.depends('width_m', 'depth_m')
    def _compute_area(self):
        for booth in self:
            booth.area_sqm = float_round((booth.width_m or 0.0) * (booth.depth_m or 0.0), precision_digits=2)

    def name_get(self):
        """Override to include event name when displaying booth names."""
        result = []
        for booth in self:
            display = booth.name
            if booth.event_id:
                display = f"{booth.event_id.display_name} / {display}"
            result.append((booth.id, display))
        return result

    def action_reset(self):
        """Reset booth to available state and clear assignment."""
        for booth in self:
            booth.write({'state': 'available', 'application_id': False})