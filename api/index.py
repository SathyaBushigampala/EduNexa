from backend.app import app

try:
    from mangum import Mangum
    handler = Mangum(app)
except Exception:
    pass

