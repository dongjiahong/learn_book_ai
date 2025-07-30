#!/usr/bin/env python3
"""
Comprehensive test runner for the RAG Learning Platform
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        print(f"\nSTDOUT:\n{result.stdout}")
    
    if result.stderr:
        print(f"\nSTDERR:\n{result.stderr}")
    
    return result.returncode == 0


def main():
    """Run comprehensive tests"""
    print("RAG Learning Platform - Comprehensive Test Suite")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir(Path(__file__).parent)
    
    # Test categories to run
    test_categories = [
        {
            "name": "Unit Tests - CRUD Operations",
            "command": "python -m pytest tests/test_crud_operations.py -v --tb=short",
            "required": True
        },
        {
            "name": "Unit Tests - Services",
            "command": "python -m pytest tests/test_services.py -v --tb=short",
            "required": True
        },
        {
            "name": "Unit Tests - Model Configuration",
            "command": "python -m pytest tests/test_model_config.py -v --tb=short",
            "required": True
        },
        {
            "name": "Unit Tests - Vector Store",
            "command": "python -m pytest tests/test_vector_store.py -v --tb=short",
            "required": True
        },
        {
            "name": "Integration Tests - API Endpoints",
            "command": "python -m pytest tests/test_api_integration.py -v --tb=short",
            "required": True
        },
        {
            "name": "Integration Tests - Authentication",
            "command": "python -m pytest tests/test_auth.py -v --tb=short",
            "required": False
        },
        {
            "name": "Existing Integration Tests",
            "command": "python -m pytest test_*integration*.py -v --tb=short",
            "required": False
        },
        {
            "name": "All Unit Tests",
            "command": "python -m pytest tests/ -v --tb=short",
            "required": False
        },
        {
            "name": "Coverage Report",
            "command": "python -m pytest tests/ --cov=app --cov-report=html --cov-report=term",
            "required": False
        }
    ]
    
    # Results tracking
    results = []
    total_tests = len(test_categories)
    passed_tests = 0
    
    # Run each test category
    for i, test_category in enumerate(test_categories, 1):
        print(f"\n[{i}/{total_tests}] {test_category['name']}")
        
        success = run_command(test_category['command'], test_category['name'])
        results.append({
            'name': test_category['name'],
            'success': success,
            'required': test_category['required']
        })
        
        if success:
            passed_tests += 1
            print(f"✅ PASSED: {test_category['name']}")
        else:
            print(f"❌ FAILED: {test_category['name']}")
            if test_category['required']:
                print("⚠️  This is a required test category!")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        required = " (REQUIRED)" if result['required'] else ""
        print(f"{status} {result['name']}{required}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test categories passed")
    
    # Check if all required tests passed
    required_failures = [r for r in results if r['required'] and not r['success']]
    
    if required_failures:
        print(f"\n❌ {len(required_failures)} required test categories failed!")
        print("Required test failures:")
        for failure in required_failures:
            print(f"  - {failure['name']}")
        return 1
    else:
        print(f"\n✅ All required tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())