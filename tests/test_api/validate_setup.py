#!/usr/bin/env python3
"""
Validation script to test imports and basic functionality before running full tests.
"""

import os
import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        # Test pytest
        import pytest

        print("✓ pytest imported successfully")

        # Test FastAPI
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        print("✓ FastAPI imported successfully")

        # Test unittest.mock
        from unittest.mock import AsyncMock, Mock, patch

        print("✓ unittest.mock imported successfully")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_project_structure():
    """Test that the project structure is as expected."""
    print("\nTesting project structure...")

    # Get project root
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"

    # Check critical paths
    paths_to_check = [
        src_path / "miramind" / "api" / "main.py",
        src_path / "miramind" / "api" / "const.py",
        project_root / "tests" / "test_api" / "test_api.py",
        project_root / "tests" / "test_api" / "conftest.py",
    ]

    all_exist = True
    for path in paths_to_check:
        if path.exists():
            print(f"✓ {path.name} exists")
        else:
            print(f"✗ {path} not found")
            all_exist = False

    return all_exist


def test_api_import():
    """Test that the main API can be imported."""
    print("\nTesting API import...")

    try:
        # Add src to path
        project_root = Path(__file__).parent.parent.parent
        src_path = project_root / "src"
        sys.path.insert(0, str(src_path))

        # Try to import the API app
        from miramind.api.main import app

        print("✓ FastAPI app imported successfully")

        # Test basic app properties
        print(f"✓ App type: {type(app)}")

        return True

    except Exception as e:
        print(f"✗ API import error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("MiraMind API Test Validation")
    print("=" * 40)

    tests = [
        ("Import Tests", test_imports),
        ("Project Structure", test_project_structure),
        ("API Import", test_api_import),
    ]

    all_passed = True
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        if not test_func():
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All validation tests passed!")
        print("You can now run the API tests with:")
        print("  python run_api_tests.py")
    else:
        print("✗ Some validation tests failed.")
        print("Please fix the issues before running the API tests.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
