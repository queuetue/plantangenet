#!/usr/bin/env python3
"""
Test runner script for the unified Omni infrastructure.
Provides convenient commands to run different test suites.
"""

import os
import sys
import subprocess
import argparse


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))

    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED")

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run Omni test suites")
    parser.add_argument("--unit", action="store_true",
                        help="Run unit tests only")
    parser.add_argument("--integration", action="store_true",
                        help="Run integration tests only")
    parser.add_argument("--performance", action="store_true",
                        help="Run performance tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--omni", action="store_true",
                        help="Run Omni-specific tests only")
    parser.add_argument("--policy", action="store_true",
                        help="Run policy tests only")
    parser.add_argument("--verbose", "-v",
                        action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true",
                        help="Run with coverage")

    args = parser.parse_args()

    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]

    if args.verbose:
        base_cmd.append("-v")

    if args.coverage:
        base_cmd.extend(
            ["--cov=plantangenet", "--cov-report=html", "--cov-report=term"])

    success = True

    if args.unit or args.all:
        cmd = base_cmd + ["-m", "unit", "tests/unit/"]
        success &= run_command(cmd, "Unit Tests")

    if args.integration or args.all:
        cmd = base_cmd + ["-m", "integration", "tests/integration/"]
        success &= run_command(cmd, "Integration Tests")

    if args.performance or args.all:
        cmd = base_cmd + ["-m", "performance"]
        success &= run_command(cmd, "Performance Tests")

    if args.omni:
        cmd = base_cmd + ["tests/unit/omni/"]
        success &= run_command(cmd, "Omni Tests")

    if args.policy:
        cmd = base_cmd + ["tests/unit/policy/"]
        success &= run_command(cmd, "Policy Tests")

    if not any([args.unit, args.integration, args.performance, args.all, args.omni, args.policy]):
        # Default: run omni tests
        cmd = base_cmd + ["tests/unit/omni/"]
        success &= run_command(cmd, "Omni Tests (Default)")

    print("\n" + "=" * 60)
    if success:
        print("🎉 All selected test suites PASSED!")
    else:
        print("💥 Some test suites FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
