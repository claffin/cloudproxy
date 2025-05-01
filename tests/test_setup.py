import os
import pytest
import ast

def test_setup_file_structure():
    """Test that setup.py has the expected structure"""
    # Get the absolute path to setup.py
    setup_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "setup.py"))
    
    # Read the file content
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Check expected content patterns
    assert '#!/usr/bin/env python' in content
    assert 'from setuptools import setup' in content
    assert 'setup(name="cloudproxy")' in content
    assert 'if __name__ == "__main__":' in content
    assert 'An error occurred during setup' in content

def test_setup_ast_structure():
    """Test that setup.py has the expected structure using AST parsing"""
    # Get the absolute path to setup.py
    setup_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "setup.py"))
    
    # Read the file content
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find import statements
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    setuptools_import = any(imp.module == 'setuptools' for imp in imports)
    assert setuptools_import, "setuptools import not found"
    
    # Find setup call
    setup_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) 
                 and isinstance(node.func, ast.Name) and node.func.id == 'setup']
    assert len(setup_calls) > 0, "setup() call not found"
    
    # Find if __name__ == "__main__" block
    main_checks = [node for node in ast.walk(tree) if isinstance(node, ast.If) 
                  and isinstance(node.test, ast.Compare)
                  and isinstance(node.test.left, ast.Name) 
                  and node.test.left.id == '__name__']
    assert len(main_checks) > 0, "if __name__ == '__main__' check not found"
    
    # Find try/except block
    try_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
    assert len(try_blocks) > 0, "try/except block not found" 