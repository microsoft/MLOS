#!/usr/bin/env python3
"""
Debug script for SSH test race conditions.

Run this to collect detailed logs about SSH test fixture behavior and port management.
"""

import logging
import subprocess
import sys
from pathlib import Path

def setup_logging():
    """Configure detailed logging for debugging."""
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ssh_test_debug.log', mode='w')
        ]
    )

    # Set specific loggers to appropriate levels
    logging.getLogger('mlos_bench.tests.services.remote.ssh').setLevel(logging.DEBUG)
    logging.getLogger('mlos_bench.tests').setLevel(logging.INFO)
    logging.getLogger('pytest_docker').setLevel(logging.INFO)

    print("Logging configured. Debug output will be saved to ssh_test_debug.log")

def run_tests():
    """Run SSH tests with debugging enabled."""
    setup_logging()

    test_dir = Path(__file__).parent / "mlos_bench" / "mlos_bench" / "tests" / "services" / "remote" / "ssh"

    cmd = [
        sys.executable, "-m", "pytest",
        "-v", "-s",  # Verbose and don't capture output
        "--tb=short",  # Short traceback format
        "--log-level=DEBUG",  # Enable pytest debug logging
        "-x",  # Stop on first failure
        str(test_dir / "test_ssh_service.py"),
        str(test_dir / "test_ssh_host_service.py"),
    ]

    print(f"Running command: {' '.join(cmd)}")
    print("=" * 80)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 130

def run_parallel_tests():
    """Run tests in parallel to reproduce race conditions."""
    setup_logging()

    test_dir = Path(__file__).parent / "mlos_bench" / "mlos_bench" / "tests" / "services" / "remote" / "ssh"

    cmd = [
        sys.executable, "-m", "pytest",
        "-v", "-s",  # Verbose and don't capture output
        "--tb=short",  # Short traceback format
        "--log-level=INFO",  # Less verbose for parallel runs
        "-n", "2",  # Run with 2 workers to increase chance of race
        "--dist", "worksteal",  # Dynamic work distribution
        str(test_dir / "test_ssh_service.py"),
        str(test_dir / "test_ssh_host_service.py"),
    ]

    print(f"Running parallel tests: {' '.join(cmd)}")
    print("=" * 80)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nParallel test run interrupted by user")
        return 130

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Debug SSH test race conditions")
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel to reproduce race conditions"
    )

    args = parser.parse_args()

    if args.parallel:
        exit_code = run_parallel_tests()
    else:
        exit_code = run_tests()

    print("\n" + "=" * 80)
    print(f"Tests completed with exit code: {exit_code}")

    if exit_code != 0:
        print("Check ssh_test_debug.log for detailed debugging information")
        print("\nKey things to look for:")
        print("1. Port changes after reboot tests")
        print("2. Connection validation failures")
        print("3. Socket connection refused errors")
        print("4. Thread IDs to track which worker has issues")

    sys.exit(exit_code)
