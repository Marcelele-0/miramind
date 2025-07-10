#!/usr/bin/env python3
"""
Test runner for API tests.

This script provides an easy way to run the API tests with proper configuration.
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_environment():
    """Set up the test environment."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"

    # Add src to Python path
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Set environment variables for testing
    os.environ.setdefault("OPENAI_API_KEY", "test-key-123")
    os.environ.setdefault("AZURE_SPEECH_KEY", "test-azure-key")
    os.environ.setdefault("AZURE_SPEECH_REGION", "test-region")

    print(f"Project root: {project_root}")
    print(f"Source path: {src_path}")
    print("Environment configured for testing")


def run_tests(test_args=None):
    """Run the API tests."""
    if test_args is None:
        test_args = []

    # Default test arguments
    default_args = ["tests/test_api/", "-v", "--tb=short", "--disable-warnings"]

    # Combine with user args
    cmd_args = ["python", "-m", "pytest"] + default_args + test_args

    print(f"Running command: {' '.join(cmd_args)}")
    print("-" * 60)

    # Run the tests
    result = subprocess.run(cmd_args, cwd=Path(__file__).parent.parent.parent)
    return result.returncode


def main():
    """Main entry point."""
    print("MiraMind API Test Runner")
    print("=" * 30)

    # Setup environment
    setup_environment()

    # Parse command line arguments
    test_args = sys.argv[1:] if len(sys.argv) > 1 else []

    if "--help" in test_args or "-h" in test_args:
        print("\nUsage:")
        print("  python run_api_tests.py [pytest_args...]")
        print("\nExamples:")
        print("  python run_api_tests.py                    # Run all tests")
        print("  python run_api_tests.py -k test_chat       # Run chat tests only")
        print("  python run_api_tests.py --cov=miramind.api # Run with coverage")
        print("  python run_api_tests.py -x                 # Stop on first failure")
        return 0

    # Run the tests
    return run_tests(test_args)


if __name__ == "__main__":
    sys.exit(main())
