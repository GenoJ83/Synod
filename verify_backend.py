import requests
import os

def test_analyze():
    url = "http://localhost:8000/analyze"
    payload = {"text": "Quantum computing is a type of computation whose operations can harness the phenomena of quantum mechanics."}
    try:
        response = requests.post(url, json=payload)
        print(f"Analyze Text Status: {response.status_code}")
        if response.status_code == 200:
            print("Analyze Text Success!")
            # print(response.json())
        else:
            print(f"Analyze Text Failed: {response.text}")
    except Exception as e:
        print(f"Error testing analyze text: {e}")

def test_analyze_file():
    url = "http://localhost:8000/analyze-file"
    # Create a dummy txt file for testing
    with open("test_lecture.txt", "w") as f:
        f.write("This is a test lecture about artificial intelligence and machine learning.")
    
    try:
        with open("test_lecture.txt", "rb") as f:
            files = {"file": ("test_lecture.txt", f, "text/plain")}
            response = requests.post(url, files=files)
            print(f"Analyze File Status: {response.status_code}")
            if response.status_code == 200:
                print("Analyze File Success!")
                # print(response.json())
            else:
                print(f"Analyze File Failed: {response.text}")
    except Exception as e:
        print(f"Error testing analyze file: {e}")
    finally:
        if os.path.exists("test_lecture.txt"):
            os.remove("test_lecture.txt")

if __name__ == "__main__":
    test_analyze()
    test_analyze_file()
