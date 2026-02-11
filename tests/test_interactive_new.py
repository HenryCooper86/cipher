import pytest
from unittest.mock import MagicMock, patch, ANY
from pwd_generator.interactive import MainMenu
from pwd_generator import SecurePasswordGenerator


@pytest.fixture
def mock_gen():
    gen = MagicMock(spec=SecurePasswordGenerator)
    gen.policy = {"max_length": 128, "expiration_days": 90}
    gen.history = []
    gen.calculate_entropy.return_value = 50.0  # Return a float
    return gen


@pytest.fixture
def menu(mock_gen):
    return MainMenu(mock_gen, "master_password")


@patch("pwd_generator.interactive.get_input")
@patch("pwd_generator.interactive.print_password_stats")
@patch("pwd_generator.interactive.copy_to_clipboard")
@patch("pwd_generator.interactive.prompt_yes_no")
def test_generate_random_password(mock_yes_no, mock_copy, mock_stats, mock_input, menu):
    # Setup inputs: length, service, notes
    mock_input.side_effect = ["16", "MyService", "MyNotes"]
    mock_yes_no.return_value = True  # Copy to clipboard: Yes, Save to history: Yes

    menu.generate_random_password()

    # Verify generator called
    menu.gen.generate_random_string.assert_called_with(16)

    # Verify stats printed
    mock_stats.assert_called()

    # Verify copied
    mock_copy.assert_called()

    # Verify saved to history
    menu.gen.add_to_history.assert_called_with(ANY, "MyService", "MyNotes")


@patch("pwd_generator.interactive.get_input")
@patch("pwd_generator.interactive.print_password_stats")
def test_generate_passphrase(mock_stats, mock_input, menu):
    mock_input.side_effect = [
        "5",
        "back",
    ]  # 5 words, then back at next prompt (if any) or just finish
    # generate_passphrase asks for num words, then copy (prompt_yes_no), then save (prompt_yes_no)
    # I need to mock prompt_yes_no too
    with patch("pwd_generator.interactive.prompt_yes_no") as mock_yes_no:
        mock_yes_no.return_value = False  # Don't copy, don't save

        menu.generate_passphrase()

        menu.gen.generate_passphrase.assert_called_with(5)


@patch("pwd_generator.interactive.get_input")
def test_generate_pin(mock_input, menu):
    mock_input.return_value = "6"
    menu.generate_pin()
    menu.gen.generate_pin.assert_called_with(6)


@patch("pwd_generator.interactive.get_input")
def test_generate_with_template(mock_input, menu):
    # Mock templates
    with patch("pwd_generator.templates.list_templates") as mock_list:
        mock_list.return_value = ["basic"]
        with patch("pwd_generator.templates.get_template") as mock_get:
            mock_template = MagicMock()
            mock_template.min_length = 8
            mock_template.generate.return_value = "password"
            mock_get.return_value = mock_template

            # Inputs: template name, length, service, notes
            mock_input.side_effect = ["basic", "12", "Svc", "Nts"]

            with patch("pwd_generator.interactive.prompt_yes_no") as mock_yes_no:
                mock_yes_no.return_value = True
                with patch("pwd_generator.interactive.print_password_stats"):
                    with patch("pwd_generator.interactive.copy_to_clipboard"):
                        menu.generate_with_template()

            mock_template.generate.assert_called_with(12)
            menu.gen.add_to_history.assert_called()


@patch("pwd_generator.interactive.get_input")
@patch("pwd_generator.interactive.safe_getpass")
def test_check_password_breach(mock_getpass, mock_input, menu):
    mock_getpass.return_value = b"password"
    menu.gen.check_password_breach.return_value = (
        False,
        {"message": "Safe", "hash_prefix": "ABCDE", "timestamp": "now"},
    )

    menu.check_password_breach()

    menu.gen.check_password_breach.assert_called_with("password")


@patch("pwd_generator.interactive.get_input")
@patch("pwd_generator.interactive.safe_getpass")
def test_analyze_custom_password(mock_getpass, mock_input, menu):
    mock_getpass.return_value = b"password"
    with patch(
        "pwd_generator.visualization.print_enhanced_password_stats"
    ) as mock_print:
        menu.analyze_custom_password()
        mock_print.assert_called()


@patch("pwd_generator.interactive.get_input")
def test_export_history(mock_input, menu):
    # Setup history
    menu.gen.history = [{"metadata": {"service": "test"}}]

    # Inputs: Apply filters? (No - handled by prompt_yes_no), Format (1=JSON), Filename, Include passwords? (Yes)
    mock_input.side_effect = ["1", "export.json"]

    with patch("pwd_generator.interactive.prompt_yes_no") as mock_yes_no:
        mock_yes_no.side_effect = [False, True]  # Filter: No, Include Passwords: True

        with patch("pwd_generator.export.export_history_json") as mock_export:
            mock_export.return_value = True

            menu.export_history()

            mock_export.assert_called()


@patch("pwd_generator.interactive.get_input")
def test_import_passwords(mock_input, menu):
    # Setup encryption
    menu.gen.encryption_manager = MagicMock()
    menu.gen.encryption_manager.cipher = True

    # Inputs: Filename, Format (2=JSON)
    mock_input.side_effect = ["import.json", "2"]

    with patch("pwd_generator.import_export.import_from_json") as mock_import:
        mock_import.return_value = [{"password": "pwd", "metadata": {}}]
        with patch("pwd_generator.validators.Path.exists", return_value=True):
            with patch("pwd_generator.validators.Path.is_absolute", return_value=True):
                menu.import_passwords()

                mock_import.assert_called()
                menu.gen.add_to_history.assert_called()
