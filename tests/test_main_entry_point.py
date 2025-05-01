import unittest
import runpy
from unittest.mock import patch

class TestMainEntryPoint(unittest.TestCase):
    @patch('cloudproxy.main.main')
    def test_main_calls_main(self, mock_main):
        # Use runpy to execute the module as the main script
        runpy.run_module('cloudproxy.__main__', run_name='__main__')
        # Check if the main function patched was called
        mock_main.assert_called_once()

if __name__ == '__main__':
    unittest.main()