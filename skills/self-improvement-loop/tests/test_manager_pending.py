import subprocess

def test_manager_pending_command_exists():
    """manager.py should have pending command to manage pending_notifications"""
    result = subprocess.run(
        ["python3", "scripts/manager.py", "--help"],
        capture_output=True, text=True
    )
    assert "pending" in result.stdout, "pending subcommand missing"

