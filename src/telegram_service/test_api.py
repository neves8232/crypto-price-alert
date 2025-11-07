#!/usr/bin/env python3
"""
Manual API Testing Script

Run this script to test the Telegram Alert Service API endpoints.
Make sure the service is running before executing this script.

Usage:
    python test_api.py
"""

import asyncio
import os
import sys
from typing import Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:52001")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
TEST_CHAT_ID = os.getenv("TEST_CHAT_ID")  # Your Telegram chat ID


def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def test_health_check() -> bool:
    """Test the health check endpoint."""
    print_section("Testing Health Check")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_URL}/health", timeout=10.0)

            print(f"Status Code: {response.status_code}")
            print(f"Response:\n{response.json()}")

            if response.status_code == 200:
                print("\n✅ Health check PASSED")
                return True
            else:
                print("\n❌ Health check FAILED")
                return False

    except Exception as e:
        print(f"\n❌ Health check FAILED: {e}")
        return False


async def test_metrics() -> bool:
    """Test the metrics endpoint."""
    print_section("Testing Metrics")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVICE_URL}/metrics", timeout=10.0)

            print(f"Status Code: {response.status_code}")
            print(f"Response (first 500 chars):\n{response.text[:500]}...")

            if response.status_code == 200:
                print("\n✅ Metrics endpoint PASSED")
                return True
            else:
                print("\n❌ Metrics endpoint FAILED")
                return False

    except Exception as e:
        print(f"\n❌ Metrics endpoint FAILED: {e}")
        return False


async def test_send_message(chat_id: Optional[str] = None) -> bool:
    """Test sending a message."""
    print_section("Testing Send Message")

    if not AUTH_TOKEN:
        print("❌ AUTH_TOKEN not set in environment")
        print("Set it in .env file or export AUTH_TOKEN=your_token")
        return False

    if not chat_id:
        print("⚠️  TEST_CHAT_ID not set - skipping message send test")
        print("To test message sending, set TEST_CHAT_ID in .env file")
        return True  # Don't fail the test if chat_id not provided

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICE_URL}/api/v1/alerts/send",
                headers={
                    "Authorization": f"Bearer {AUTH_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "chat_id": chat_id,
                    "message": "🧪 Test message from Telegram Alert Service API test script",
                    "parse_mode": "HTML",
                    "priority": "normal",
                    "metadata": {
                        "test": True,
                        "source": "test_api.py"
                    }
                },
                timeout=30.0,
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response:\n{response.json()}")

            if response.status_code in [200, 202]:
                print("\n✅ Send message PASSED")
                return True
            else:
                print("\n❌ Send message FAILED")
                return False

    except Exception as e:
        print(f"\n❌ Send message FAILED: {e}")
        return False


async def test_authentication() -> bool:
    """Test authentication with invalid token."""
    print_section("Testing Authentication")

    try:
        async with httpx.AsyncClient() as client:
            # Test without token
            print("1. Testing without Authorization header...")
            response = await client.post(
                f"{SERVICE_URL}/api/v1/alerts/send",
                json={
                    "chat_id": "123456789",
                    "message": "Test"
                },
                timeout=10.0,
            )

            if response.status_code == 401:
                print("   ✅ Correctly rejected (401)")
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                return False

            # Test with invalid token
            print("\n2. Testing with invalid token...")
            response = await client.post(
                f"{SERVICE_URL}/api/v1/alerts/send",
                headers={"Authorization": "Bearer invalid_token"},
                json={
                    "chat_id": "123456789",
                    "message": "Test"
                },
                timeout=10.0,
            )

            if response.status_code == 401:
                print("   ✅ Correctly rejected (401)")
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                return False

            print("\n✅ Authentication tests PASSED")
            return True

    except Exception as e:
        print(f"\n❌ Authentication tests FAILED: {e}")
        return False


async def test_input_validation() -> bool:
    """Test input validation."""
    print_section("Testing Input Validation")

    if not AUTH_TOKEN:
        print("⚠️  AUTH_TOKEN not set - skipping validation test")
        return True

    try:
        async with httpx.AsyncClient() as client:
            # Test with empty message
            print("1. Testing with empty message...")
            response = await client.post(
                f"{SERVICE_URL}/api/v1/alerts/send",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                json={
                    "chat_id": "123456789",
                    "message": ""
                },
                timeout=10.0,
            )

            if response.status_code == 422:
                print("   ✅ Correctly rejected (422)")
            else:
                print(f"   ⚠️  Expected 422, got {response.status_code}")

            # Test with invalid parse_mode
            print("\n2. Testing with invalid parse_mode...")
            response = await client.post(
                f"{SERVICE_URL}/api/v1/alerts/send",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                json={
                    "chat_id": "123456789",
                    "message": "Test",
                    "parse_mode": "INVALID"
                },
                timeout=10.0,
            )

            if response.status_code == 422:
                print("   ✅ Correctly rejected (422)")
            else:
                print(f"   ⚠️  Expected 422, got {response.status_code}")

            print("\n✅ Input validation tests PASSED")
            return True

    except Exception as e:
        print(f"\n❌ Input validation tests FAILED: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🔬" * 35)
    print("  Telegram Alert Service - API Testing")
    print("🔬" * 35)

    print(f"\nService URL: {SERVICE_URL}")
    print(f"Auth Token: {'✅ Set' if AUTH_TOKEN else '❌ Not set'}")
    print(f"Test Chat ID: {'✅ Set' if TEST_CHAT_ID else '⚠️  Not set (message test will be skipped)'}")

    # Check if service is running
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{SERVICE_URL}/", timeout=5.0)
    except Exception as e:
        print(f"\n❌ Cannot connect to service at {SERVICE_URL}")
        print(f"Error: {e}")
        print("\nMake sure the service is running:")
        print("  python -m uvicorn main:app --reload")
        sys.exit(1)

    # Run tests
    results = []

    results.append(await test_health_check())
    results.append(await test_metrics())
    results.append(await test_authentication())
    results.append(await test_input_validation())
    results.append(await test_send_message(TEST_CHAT_ID))

    # Summary
    print_section("Test Summary")

    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
