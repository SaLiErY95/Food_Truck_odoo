"""
Initialize the food_truck_festival module.

This module bundles together all sub‑packages and models required for the
Food Truck Festival workflow.  Models are imported here so that Odoo
automatically registers them on module installation.
"""

from . import models
from . import controllers