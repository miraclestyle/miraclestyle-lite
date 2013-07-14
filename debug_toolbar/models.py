from django.conf import settings
from django.utils.importlib import import_module

from debug_toolbar.toolbar.loader import load_panel_classes
from debug_toolbar.middleware import DebugToolbarMiddleware

loaded = True
 
def is_toolbar(cls):
    return (issubclass(cls, DebugToolbarMiddleware) or
            DebugToolbarMiddleware in getattr(cls, '__bases__', ()))