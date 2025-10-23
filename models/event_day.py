"""
Represent individual days of an event for scheduling and attendance.

The standard event model stores only a start and end date.  To allow
vendors to select on which days they will attend, we use a helper
model that enumerates the dates between the begin and end.  Records
can be created manually or generated via a method on the event.
"""

from odoo import models, fields, api


class FoodEventDay(models.Model):
    _name = 'food.event.day'
    _description = 'Food Festival Event Day'
    _order = 'event_id, date'

    event_id = fields.Many2one('event.event', required=True, ondelete='cascade')
    date = fields.Date(required=True)
    name = fields.Char(compute='_compute_name', store=True)

    @api.depends('event_id', 'date')
    def _compute_name(self):
        for day in self:
            if day.event_id and day.date:
                day.name = f"{day.event_id.display_name} - {day.date}"
            else:
                day.name = day.date or ''