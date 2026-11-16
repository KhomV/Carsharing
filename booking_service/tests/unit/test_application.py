def test_application_builds_http_routes():
    # Catches dependency types that FastAPI cannot resolve at startup.
    from app.main import app

    schema = app.openapi()
    assert '/api/cars' in schema['paths']
    assert '/api/bookings' in schema['paths']
    assert 'telemetry_client' not in str(schema['paths'])
