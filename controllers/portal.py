"""
Portal controllers for vendors to manage their festival applications.

Authenticated portal users can view their submissions, download
contracts and invoices, pay invoices, upload missing documents and
check their booth assignment.  There is also a check‑in endpoint
consumed by QR codes at the event.
"""

from odoo import http, _
from odoo.http import request


class FoodFestivalPortal(http.Controller):
    @http.route('/my/food', type='http', auth='user', website=True)
    def portal_food_list(self, **kw):
        user_partner = request.env.user.partner_id.commercial_partner_id
        applications = request.env['food.vendor.application'].sudo().search([
            ('partner_id', 'child_of', user_partner.id)
        ])
        return request.render('food_truck_festival.portal_applications', {
            'applications': applications,
        })

    @http.route('/my/food/<int:application_id>', type='http', auth='user', website=True)
    def portal_food_detail(self, application_id, **post):
        application = request.env['food.vendor.application'].sudo().browse(application_id)
        user_partner = request.env.user.partner_id.commercial_partner_id
        if application.partner_id.commercial_partner_id != user_partner:
            return request.render('website.403')
        return request.render('food_truck_festival.portal_application_detail', {
            'application': application,
        })

    @http.route('/food/checkin/<string:token>', type='http', auth='public', website=True)
    def food_checkin(self, token, **kw):
        app = request.env['food.vendor.application'].sudo().search([('portal_token', '=', token)], limit=1)
        if not app:
            return request.render('website.404')
        # mark check in
        if app.state not in ('checked_in', 'closed'):
            app.action_check_in()
        return request.render('food_truck_festival.checkin_confirmation', {
            'application': app,
        })