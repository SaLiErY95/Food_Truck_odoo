"""
Model package for the Food Truck Festival module.

This package aggregates all model definitions so they can be imported
from the package root.  Each model file is separated by business
domain to ease maintenance: applications, booths, events and
service lines.
"""

from . import event
from . import booth
from . import service_line
from . import vendor_application
from . import event_day