import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from pwd_generator.breach_check import check_password_breach


class TestBreachCheck(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_check_password_breach_found(self, mock_urlopen):
        # Setup mock response
        # Let's say password is "password"
        # SHA1("password") = 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
        # Prefix: 5BAA6
        # Suffix: 1E4C9B93F3F0682250B6CF8331B7EE68FD8

        mock_response = MagicMock()
        # Return a response that includes our suffix
        mock_response.read.return_value = (
            b"1E4C9B93F3F0682250B6CF8331B7EE68FD8:100\r\nOTHERHASH:5"
        )
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        is_breached, result = check_password_breach("password")

        self.assertTrue(is_breached)
        self.assertEqual(result["count"], 100)
        self.assertTrue("breached" in result["message"].lower())
        self.assertEqual(result["hash_prefix"], "5BAA6")

    @patch("urllib.request.urlopen")
    def test_check_password_breach_not_found(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"OTHERHASH:5\r\nANOTHERONE:10"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        is_breached, result = check_password_breach("safe_password_123")

        self.assertFalse(is_breached)
        self.assertEqual(result["count"], 0)
        self.assertTrue("not found" in result["message"].lower())

    @patch("urllib.request.urlopen")
    def test_check_password_breach_api_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        is_breached, result = check_password_breach("password")

        self.assertFalse(is_breached)
        self.assertIsNotNone(result["error"])
        self.assertTrue("Unable to check" in result["message"])

    @patch("urllib.request.urlopen")
    def test_check_password_breach_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("Timed out")

        is_breached, result = check_password_breach("password")

        self.assertFalse(is_breached)
        self.assertIsNotNone(result["error"])
        self.assertTrue("timed out" in result["message"])

    @patch("urllib.request.urlopen")
    def test_check_password_breach_encoding_error(self, mock_urlopen):
        mock_response = MagicMock()
        # Invalid UTF-8 sequence
        mock_response.read.return_value = b"\xff\xff"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        is_breached, result = check_password_breach("password")

        self.assertFalse(is_breached)
        self.assertIsNotNone(result["error"])
        self.assertTrue("encoding error" in result["message"].lower())

    @patch("hashlib.sha1")
    def test_check_password_breach_unexpected_error(self, mock_sha1):
        mock_sha1.side_effect = Exception("Unexpected")

        is_breached, result = check_password_breach("password")

        self.assertFalse(is_breached)
        self.assertIsNotNone(result["error"])
        self.assertTrue("Error checking breach" in result["message"])
