"""
Extend the core event model with festival specific fields.

The event model is inherited rather than wrapped so that it
retains compatibility with other apps (event tickets, booths,
schedule).  Additional fields allow organisers to upload a map
image, define rules and instructions, and set a default power
allocation per booth.  These fields are used when assigning
booths and preparing documentation for vendors.
"""

from odoo import fields, models


class EventEvent(models.Model):
    """
    Inherit from ``event.event`` to add configuration specific to
    street food festivals.  The additional fields are optional and
    appear on the event form in a dedicated "Food Festival" page.
    """

    _inherit = 'event.event'

    map_image = fields.Binary(
        string='Map Image',
        help='Upload a floor plan or venue map.  Used for booth placement and portal display.',
    )
    rules_html = fields.Html(
        string='Event Rules',
        translate=True,
        help='HTML content describing festival rules.  Displayed to vendors in the portal.',
    )
    checkin_instructions = fields.Html(
        string='Check‑In Instructions',
        translate=True,
        help='Detailed instructions for vendors to check‑in on the day of the event.',
    )
    default_kwh_per_booth = fields.Float(
        string='Default kW per Booth',
        help='Default power (kW) allocated to each booth if not specified individually.',
        default=2.0,
    )

    food_event_day_ids = fields.One2many(
        'food.event.day',
        'event_id',
        string='Event Days',
        help='List of individual days for this event.  Vendors select which days they will attend.',
    )