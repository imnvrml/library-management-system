"""Application factory smoke tests (NFR-08: the app starts with only the packages in requirements.txt)."""
from library import create_app


def test_create_app_with_a_new_database_file(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True})
    con = app.extensions["library_db"].connection()
    assert con.execute("SELECT COUNT(*) FROM user").fetchone()[0] == 0


def test_init_db_command_is_repeatable(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True})
    runner = app.test_cli_runner()
    assert "Database ready" in runner.invoke(args=["init-db"]).output
    assert "Database ready" in runner.invoke(args=["init-db"]).output


def test_seed_demo_creates_data_once(tmp_path):
    """Regression test for D-02 (duplicate copy codes in the demo data)."""
    app = create_app({"DATABASE": str(tmp_path / "demo.db"), "TESTING": True})
    runner = app.test_cli_runner()
    assert "Demo data created" in runner.invoke(args=["seed-demo"]).output
    assert "already present" in runner.invoke(args=["seed-demo"]).output
    services = app.extensions["library"]
    assert len(services.users.members()) == 3
    assert len(services.circulation.overdue_loans()) == 1
