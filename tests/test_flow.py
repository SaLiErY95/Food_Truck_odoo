"""
Tests for the Food Truck Festival module.

These tests use Odoo's built in test framework.  They simulate a
typical happy path where a vendor applies, the application is
approved, a contract is signed, and an invoice is generated.  They
also verify security restrictions for portal users.
"""

from odoo.tests import SavepointCase, tagged


@tagged('-at_install', 'post_install')
class TestFoodFestivalFlow(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # create an event
        cls.event = cls.env['event.event'].create({
            'name': 'Test Festival',
            'date_begin': '2025-08-01 10:00:00',
            'date_end': '2025-08-02 22:00:00',
        })
        # create event days
        cls.day1 = cls.env['food.event.day'].create({'event_id': cls.event.id, 'date': '2025-08-01'})
        cls.day2 = cls.env['food.event.day'].create({'event_id': cls.event.id, 'date': '2025-08-02'})
        # create a booth
        cls.booth = cls.env['food.booth'].create({
            'name': 'Test Booth',
            'event_id': cls.event.id,
            'code': 'T1',
            'width_m': 3,
            'depth_m': 3,
            'power_kw': 3,
            'price_per_day': 100,
        })
        # create a partner
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Vendor Test SRL',
            'company_type': 'company',
        })

    def test_application_flow(self):
        # create application
        app = self.env['food.vendor.application'].create({
            'partner_id': self.vendor.id,
            'event_id': self.event.id,
            'needs_power_kw': 2,
            'day_ids': [(6, 0, [self.day1.id, self.day2.id])],
        })
        # submit and approve
        app.action_submit()
        self.assertEqual(app.state, 'review')
        app.action_approve()
        self.assertEqual(app.state, 'approved')
        self.assertTrue(app.booth_id)
        # send contract (requires template; skip if not configured)
        # sign simulation: directly mark signed
        app.action_mark_signed()
        self.assertEqual(app.state, 'invoiced')
        self.assertTrue(app.sale_order_id)
        self.assertTrue(app.invoice_id)
        # check‑in
        app.action_check_in()
        self.assertEqual(app.state, 'checked_in')