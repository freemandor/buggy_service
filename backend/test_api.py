"""Quick API test script to verify backend is working."""
import json
import requests

BASE_URL = "http://localhost:8000/api"


def test_backend():
    print("Testing Backend APIs...\n")

    # 1. Test login
    print("1. Testing login endpoint...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"username": "dispatcher", "password": "dispatcher"},
    )
    print(f"   Status: {login_response.status_code}")
    if login_response.status_code == 200:
        token = login_response.json()["access"]
        print("   ✓ Login successful, token received")
    else:
        print(f"   ✗ Login failed: {login_response.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test /auth/me/
    print("\n2. Testing /auth/me/ endpoint...")
    me_response = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
    print(f"   Status: {me_response.status_code}")
    if me_response.status_code == 200:
        user = me_response.json()
        print(f"   ✓ User: {user['username']} ({user['role']})")
    else:
        print(f"   ✗ Failed: {me_response.text}")

    # 3. Test /buggies/
    print("\n3. Testing /buggies/ endpoint...")
    buggies_response = requests.get(f"{BASE_URL}/buggies/", headers=headers)
    print(f"   Status: {buggies_response.status_code}")
    if buggies_response.status_code == 200:
        buggies = buggies_response.json()
        print(f"   ✓ Found {len(buggies)} buggy(s)")
        for buggy in buggies:
            location = buggy["current_poi"]["name"] if buggy["current_poi"] else "unknown"
            print(f"      - {buggy['display_name']}: {buggy['status']} at {location}")
    else:
        print(f"   ✗ Failed: {buggies_response.text}")

    # 4. Test /rides/
    print("\n4. Testing /rides/ endpoint...")
    rides_response = requests.get(f"{BASE_URL}/rides/", headers=headers)
    print(f"   Status: {rides_response.status_code}")
    if rides_response.status_code == 200:
        rides = rides_response.json()
        print(f"   ✓ Found {len(rides)} ride(s)")
    else:
        print(f"   ✗ Failed: {rides_response.text}")

    # 5. Test creating a ride
    print("\n5. Testing /rides/create-and-assign/ endpoint...")
    ride_data = {
        "pickup_poi_code": "RECEPTION",
        "dropoff_poi_code": "BEACH_BAR",
        "num_guests": 2,
        "room_number": "101",
        "guest_name": "Test Guest",
    }
    create_response = requests.post(
        f"{BASE_URL}/rides/create-and-assign/",
        headers=headers,
        json=ride_data,
    )
    print(f"   Status: {create_response.status_code}")
    if create_response.status_code == 201:
        result = create_response.json()
        print(f"   ✓ Ride {result['ride']['public_code']} assigned to {result['assigned_buggy']['display_name']}")
    else:
        print(f"   ✗ Failed: {create_response.text}")

    # 6. Test metrics
    print("\n6. Testing /metrics/summary/ endpoint...")
    metrics_response = requests.get(f"{BASE_URL}/metrics/summary/", headers=headers)
    print(f"   Status: {metrics_response.status_code}")
    if metrics_response.status_code == 200:
        metrics = metrics_response.json()
        print(f"   ✓ Date: {metrics['date']}, Total rides: {metrics['total_rides']}")
    else:
        print(f"   ✗ Failed: {metrics_response.text}")

    print("\n✓ Backend API tests completed!")


if __name__ == "__main__":
    try:
        test_backend()
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to backend. Is the server running?")
    except Exception as e:
        print(f"✗ Error: {e}")
