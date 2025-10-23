"""
Manifest for the Food Truck Festival module.

This manifest declares the module's metadata, dependencies and data
files.  The version number follows the Odoo semantic versioning
convention: major.minor.patch.series.  See the README in
static/description/index.html for usage instructions and screenshots.
"""

{
    'name': 'Food Truck Festival',
    'version': '18.0.1.0',
    'author': 'AC Check‑OUT Solution SRL',
    'website': 'https://www.check-outeam.ro',
    'summary': 'Vendor registration, booth allocation, contracts and invoicing for street food festivals',
    'description': """
        The Food Truck Festival module provides an end‑to‑end workflow for
        managing food vendor registrations at events.  It covers public
        applications, approval, automatic booth assignment, e‑signature
        contracts, sales order and invoice generation, vendor portal
        access, badge printing and on‑site check‑in.  Organisers gain
        dashboards to track performance and vendors enjoy a modern
        self‑service experience.
    """,
    'category': 'Sales/Event',
    'license': 'OEEL-1',
    'support': 'support@check-outeam.ro',
    'depends': [
        'base',
        'contacts',
        'website',
        'portal',
        'event',
        'sale',
        'account',
        'sign',
        'web',
    ],
    'data': [
        'security/food_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/mail_templates.xml',
        'data/sign_templates.xml',
        'data/automations.xml',
        'views/menu.xml',
        'views/vendor_application_views.xml',
        'views/booth_views.xml',
        'views/event_views_inherit.xml',
        'views/portal_templates.xml',
        'views/sign_templates.xml',
        'views/report_badge.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'food_truck_festival/static/src/js/portal.js',
            'food_truck_festival/static/src/css/portal.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}