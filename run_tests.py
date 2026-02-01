#!/usr/bin/env python3
"""
Test runner script for the Knowledge Summary System

Run all tests or specific test modules with detailed reporting.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py youtube      # Run YouTube extractor tests
    python run_tests.py pdf          # Run PDF extractor tests
    python run_tests.py --coverage   # Run with coverage report
    python run_tests.py --verbose    # Run with verbose output
"""

import sys
import subprocess
from pathlib import Path


def run_pytest(test_path=None, coverage=False, verbose=False):
    """Run pytest with specified options"""

    cmd = ["python", "-m", "pytest"]

    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])

    # Add verbosity
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Add test path or run all
    if test_path:
        cmd.append(f"tests/test_{test_path}.py")
    else:
        cmd.append("tests/")

    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def run_specific_test_class(test_class=None):
    """Run a specific test class"""
    if not test_class:
        print("Error: No test class specified")
        return 1

    cmd = ["python", "-m", "pytest", "-v", f"tests/::{test_class}"]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def run_unit_tests_only():
    """Run only unit tests (marked with 'unit')"""
    cmd = ["python", "-m", "pytest", "-v", "-m", "unit", "tests/"]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def run_integration_tests_only():
    """Run only integration tests (marked with 'integration')"""
    cmd = ["python", "-m", "pytest", "-v", "-m", "integration", "tests/"]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def list_all_tests():
    """List all available test modules"""
    test_dir = Path(__file__).parent / "tests"
    test_files = sorted(test_dir.glob("test_*.py"))

    print("\n" + "=" * 60)
    print("Available Test Modules")
    print("=" * 60)

    for test_file in test_files:
        module_name = test_file.stem
        category = module_name.replace("test_", "").replace("_", " ").title()
        print(f"  • {category:30s} ({module_name})")

    print("\nUsage:")
    print("  python run_tests.py <module_name>")
    print("  python run_tests.py --all")
    print("=" * 60 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests for Knowledge Summary System"
    )
    parser.add_argument(
        "module",
        nargs="?",
        help="Test module to run (e.g., youtube, pdf, ollama_summarizer)",
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Generate coverage report"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all available test modules"
    )
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )

    args = parser.parse_args()

    # List all tests if requested
    if args.list:
        list_all_tests()
        return 0

    # Run specific test type
    if args.unit:
        print("Running unit tests only...\n")
        return run_unit_tests_only()

    if args.integration:
        print("Running integration tests only...\n")
        return run_integration_tests_only()

    # Run specific module or all tests
    module = args.module
    if module:
        print(f"Running test module: {module}\n")
        return run_pytest(
            test_path=module, coverage=args.coverage, verbose=args.verbose
        )
    else:
        print("Running all tests...\n")
        return run_pytest(coverage=args.coverage, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
