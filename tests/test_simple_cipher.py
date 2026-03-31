import unittest
import sys
import os
import string
import math
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent directory to path to import simple_cipher as simple_pwd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import simple_cipher as simple_pwd

class TestSimplePwd(unittest.TestCase):
    def test_calculate_entropy(self):
        # Empty password
        self.assertEqual(simple_pwd.calculate_entropy(""), 0)
        
        # Lowercase only (26 chars) -> log2(26) ≈ 4.7 bits per char * 3 chars ≈ 14.1
        entropy = simple_pwd.calculate_entropy("abc")
        self.assertAlmostEqual(entropy, 14.101, places=3)
        
        # Mixed (lower + upper + digits + special) -> log2(79) ≈ 6.30 bits per char
        # entropy of 1 char from full set
        # "A" has upper only -> pool 26 -> 4.7 bits
        self.assertAlmostEqual(simple_pwd.calculate_entropy("A"), 4.7004, places=3)
        
        # "Aa1!" has all types -> pool 26+26+10+17 = 79
        entropy_complex = simple_pwd.calculate_entropy("Aa1!")
        expected = 4 * math.log2(79)  # log2(79) * 4
        self.assertAlmostEqual(entropy_complex, expected, places=1)

    def test_generate_password_length(self):
        pwd = simple_pwd.generate_password(length=20)
        self.assertEqual(len(pwd), 20)
        
        pwd = simple_pwd.generate_password(length=8)
        self.assertEqual(len(pwd), 8)

    def test_generate_password_complexity(self):
        # Should contain all types by default
        for _ in range(5):  # Try a few times to be sure
            pwd = simple_pwd.generate_password(length=50)
            self.assertTrue(any(c.isupper() for c in pwd))
            self.assertTrue(any(c.islower() for c in pwd))
            self.assertTrue(any(c.isdigit() for c in pwd))
            self.assertTrue(any(c in string.punctuation for c in pwd))

    def test_generate_password_options(self):
        # No special chars
        pwd = simple_pwd.generate_password(length=20, use_special=False)
        self.assertFalse(any(c in string.punctuation for c in pwd))
        self.assertEqual(len(pwd), 20)

    def test_generate_passphrase(self):
        # Default 4 words
        phrase = simple_pwd.generate_passphrase(words=4)
        # Structure: word-word-word-word{number}{special}
        # e.g. "Acid-Base-Code-Deck42!"
        parts = phrase.split('-')
        # The last part will contain the number and special char attached to the last word
        self.assertTrue(len(parts) >= 4) 
        
        # Check simple length constraints
        phrase5 = simple_pwd.generate_passphrase(words=5)
        self.assertTrue(len(phrase5.split('-')) >= 5)

    def test_generate_pin(self):
        pin = simple_pwd.generate_pin(length=6)
        self.assertEqual(len(pin), 6)
        self.assertTrue(pin.isdigit())
        
        pin4 = simple_pwd.generate_pin(length=4)
        self.assertEqual(len(pin4), 4)
        self.assertTrue(pin4.isdigit())

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_cli_password(self, mock_stdout):
        test_args = ["simple_pwd.py", "password", "-l", "12"]
        with patch.object(sys, 'argv', test_args):
            simple_pwd.main()
            output = mock_stdout.getvalue().strip()
            self.assertEqual(len(output), 12)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_cli_pin(self, mock_stdout):
        test_args = ["simple_pwd.py", "pin", "-l", "8"]
        with patch.object(sys, 'argv', test_args):
            simple_pwd.main()
            output = mock_stdout.getvalue().strip()
            self.assertEqual(len(output), 8)
            self.assertTrue(output.isdigit())

    @patch('builtins.input', side_effect=['4']) # Exit
    @patch('sys.exit')
    def test_interactive_exit(self, mock_exit, mock_input):
        # Just run to make sure it doesn't crash
        try:
            simple_pwd.interactive_mode()
        except:
            pass
        mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()
