import pytest
from app import create_app, db  # adjust import to your app factory

@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for testing"""
    app = create_app("testing")  # uses TestingConfig

    with app.app_context():
        db.create_all()  # setup schema
        yield app
        db.session.remove()
        db.drop_all()  # teardown


@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI runner"""
    return app.test_cli_runner()



from flask import url_for

def test_landing_page(client):
    """Landing page should load successfully"""
    resp = client.get(url_for("dashboard.landing"))
    assert resp.status_code == 200
    assert b"landing" in resp.data.lower()  # check template content

def test_home_requires_login(client):
    """Home should redirect if not logged in"""
    resp = client.get(url_for("dashboard.home"))
    assert resp.status_code == 302  # redirect to login

def test_select_db_post_invalid(client):
    """Posting invalid form should flash error and redirect"""
    resp = client.post(url_for("dashboard.select_db"), data={})
    assert resp.status_code == 302
    # could check flashed messages if you configure session

def test_delete_db(client):
    """Delete DB should redirect to home"""
    resp = client.post(url_for("dashboard.delete_db"), data={"db": "test"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(url_for("dashboard.home"))

def test_billing_page_requires_login(client):
    """Billing page requires login"""
    resp = client.get(url_for("dashboard.billing"))
    assert resp.status_code == 302

def test_submit_proof(client):
    """Submit proof should call processor and redirect"""
    resp = client.post(url_for("dashboard.submit_proof"), data={"proof": "dummy"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(url_for("dashboard.billing"))