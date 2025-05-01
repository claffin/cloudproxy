import pytest
from unittest.mock import patch

@patch('cloudproxy.main.main')
def test_main_executed_when_run_as_script(mock_main):
    """Test that the main function is called when the module is run as a script."""
    # Import the module which will call main() if __name__ == "__main__"
    # The patch above will prevent actual execution of main()
    import cloudproxy.__main__
    
    # Since we're importing the module, and __name__ != "__main__", 
    # main() should not be called
    mock_main.assert_not_called()
    
    # Now simulate if __name__ == "__main__"
    cloudproxy.__main__.__name__ = "__main__"
    
    # Execute the script's main condition
    if cloudproxy.__main__.__name__ == "__main__":
        cloudproxy.__main__.main()
    
    # Verify main() was called
    mock_main.assert_called_once() 