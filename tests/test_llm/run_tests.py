#!/usr/bin/env python3
"""
Test runner for MiraMind LLM/LangGraph test suite.
Provides easy commands to run different types of tests.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"\n✅ {description or 'Command'} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="MiraMind LLM Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--slow", action="store_true", help="Run slow tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", "-f", help="Run specific test file")
    parser.add_argument("--test", "-t", help="Run specific test")
    parser.add_argument("--debug", action="store_true", help="Run with debugger")
    parser.add_argument(
        "--html-coverage", action="store_true", help="Generate HTML coverage report"
    )

    args = parser.parse_args()

    # Get the test directory
    test_dir = Path(__file__).parent

    # Base pytest command
    base_cmd = ["pytest", str(test_dir)]

    # Add verbose flag
    if args.verbose:
        base_cmd.append("-v")

    # Add debug flag
    if args.debug:
        base_cmd.append("--pdb")

    # Coverage options
    if args.coverage or args.html_coverage:
        base_cmd.extend(["--cov=src.miramind.llm.langgraph", "--cov-report=term-missing"])

        if args.html_coverage:
            base_cmd.append("--cov-report=html")

    # Test selection
    if args.file:
        base_cmd.append(f"{test_dir}/{args.file}")

    if args.test:
        base_cmd.append(f"-k {args.test}")

    # Run specific test categories
    success = True

    if args.unit or args.all:
        cmd = base_cmd + ["-m", "unit"]
        success &= run_command(" ".join(cmd), "Unit Tests")

    if args.integration or args.all:
        cmd = base_cmd + ["-m", "integration", "--run-integration"]
        success &= run_command(" ".join(cmd), "Integration Tests")

    if args.performance or args.all:
        cmd = base_cmd + ["-m", "performance", "--run-performance"]
        success &= run_command(" ".join(cmd), "Performance Tests")

    if args.slow or args.all:
        cmd = base_cmd + ["-m", "slow", "--run-slow"]
        success &= run_command(" ".join(cmd), "Slow Tests")

    # If no specific category was selected, run default tests
    if not any([args.unit, args.integration, args.performance, args.slow, args.all]):
        if args.file or args.test:
            success &= run_command(" ".join(base_cmd), "Specific Tests")
        else:
            # Run unit tests by default
            cmd = base_cmd + ["-m", "unit"]
            success &= run_command(" ".join(cmd), "Unit Tests (Default)")

    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)

    if args.html_coverage:
        print("\n📊 HTML coverage report generated in htmlcov/index.html")

    print(f"{'='*60}")


if __name__ == "__main__":
    main()
