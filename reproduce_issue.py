import requests
import json

def test_search():
    url = "http://127.0.0.1:8000/classify"
    payload = {
        "query": "construcción",
        "actividades_reales": "albañilería",
        "procesos_criticos": ""
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        print(f"Sending POST to {url} with payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response JSON keys:", data.keys())
            if 'results' in data:
                print(f"Results found: {len(data['results'])}")
                if len(data['results']) > 0:
                    print("First result:", data['results'][0])
            else:
                print("No 'results' key in response!")
        else:
            print("Error response:", response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_search()
