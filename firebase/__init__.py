"""Firebase integration modules."""

# Re-export for backward compatibility
try:
    from .auth import FirebaseAuth
    from .data_layer import FirebaseDataLayer
    from .client import FirebaseClient
    __all__ = ['FirebaseAuth', 'FirebaseDataLayer', 'FirebaseClient']
except ImportError:
    __all__ = []
