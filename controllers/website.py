"""
Controllers for the public website functionality of the food festival.

Handles the registration form that prospective vendors use to apply
for a booth.  The form displays event details and allows vendors to
choose their attendance days and specify their requirements.  Upon
submission it creates an application record and sends a confirmation
email.
"""

from odoo import http, _
from odoo.http import request


class FoodFestivalWebsite(http.Controller):
    @http.route('/food/apply', type='http', auth='public', website=True, sitemap=True)
    def food_apply(self, event_id=None, **post):
        """Display the vendor application form and handle submission."""
        Event = request.env['event.event']
        Application = request.env['food.vendor.application']
        context = {}
        if request.httprequest.method == 'POST':
            # Handle form submission
            values = {
                'company_name_fallback': post.get('company_name'),
                'vat_fallback': post.get('vat'),
                'phone_fallback': post.get('phone'),
                'email_fallback': post.get('email'),
                'menu_description': post.get('menu_description'),
                'truck_width': float(post.get('truck_width') or 0.0),
                'truck_depth': float(post.get('truck_depth') or 0.0),
                'needs_power_kw': float(post.get('needs_power_kw') or 0.0),
                'needs_water': bool(post.get('needs_water')),
                'needs_sewage': bool(post.get('needs_sewage')),
            }
            # Determine event
            if post.get('event_id'):
                event = Event.browse(int(post['event_id']))
            else:
                event = Event.sudo().search([('is_published', '=', True)], order='date_begin desc', limit=1)
            if not event:
                return request.render('website.404')
            values['event_id'] = event.id
            # Selected days
            day_ids = []
            for key, val in post.items():
                if key.startswith('day_') and val:
                    day_id = int(key.split('_')[1])
                    day_ids.append(day_id)
            values['day_ids'] = [(6, 0, day_ids)]
            # Create application with sudo to allow website user
            Application.sudo().create(values)
            return request.render('food_truck_festival.application_thankyou', {'event': event})
        # Display form
        # Determine event
        if event_id:
            event = Event.browse(int(event_id))
        else:
            event = Event.sudo().search([('is_published', '=', True)], order='date_begin desc', limit=1)
        if not event:
            return request.render('website.404')
        # Get event days
        days = request.env['food.event.day'].sudo().search([('event_id', '=', event.id)])
        context.update({
            'event': event,
            'days': days,
        })
        return request.render('food_truck_festival.application_form', context)