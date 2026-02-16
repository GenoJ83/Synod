import requests
import sys

BASE_URL = "http://localhost:8000"

def test_auth():
    print("Testing Authentication Endpoints...")
    
    # 1. Register
    email = "testuser@example.com"
    password = "securepassword123"
    full_name = "Test User"
    
    print(f"\n[1] Registering user: {email}")
    try:
        reg_response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": full_name}
        )
        
        if reg_response.status_code == 200:
            print("✅ Registration Successful")
            print("Response:", reg_response.json())
        elif reg_response.status_code == 400 and "already registered" in reg_response.text:
             print("⚠️ User already registered (Expected if running multiple times)")
        else:
            print(f"❌ Registration Failed: {reg_response.status_code} - {reg_response.text}")
            
    except Exception as e:
        print(f"❌ Registration Error: {e}")
        return

    # 2. Login
    print(f"\n[2] Logging in user: {email}")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("token")
            print("✅ Login Successful")
            print(f"Token: {token[:20]}...")
            
            # 3. Verify Token
            print("\n[3] Verifying Token...")
            verify_response = requests.post(
                f"{BASE_URL}/auth/verify",
                json={"token": token}
            )
            if verify_response.status_code == 200:
                 print("✅ Token Verified")
                 print("User:", verify_response.json())
            else:
                 print(f"❌ Token Verification Failed: {verify_response.status_code}")

        else:
            print(f"❌ Login Failed: {login_response.status_code} - {login_response.text}")
            
    except Exception as e:
        print(f"❌ Login Error: {e}")

if __name__ == "__main__":
    test_auth()
