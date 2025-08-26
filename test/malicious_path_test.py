import unittest
from flask import Flask, request
from auth import is_safe_url

class TestSafeUrl(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_is_safe_url(self):
        with self.app.test_request_context('http://localhost/'):
            self.assertTrue(is_safe_url('/dashboard'))
            self.assertTrue(is_safe_url('http://localhost/profile'))
            self.assertFalse(is_safe_url('http://danger.com'))
            self.assertFalse(is_safe_url('javascript:alert(1)'))
            self.assertFalse(is_safe_url('JaVaScRiPt:alert(1)'))
            self.assertFalse(is_safe_url('data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=='))
            self.assertFalse(is_safe_url('javascript:document.cookie'))

            

if __name__ == '__main__':
    unittest.main()