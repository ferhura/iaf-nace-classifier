from fastapi.testclient import TestClient
from iaf_nace_classifier.api import app

client = TestClient(app)

def test_legacy_get():
    print("Testing GET /classify?code=24.46...")
    response = client.get("/classify?code=24.46")
    assert response.status_code == 200
    data = response.json()
    assert data["input"] == "24.46"
    assert data["result"]["codigo_iaf"] is not None
    print("PASS")

def test_legacy_post():
    print("Testing POST /classify with code...")
    response = client.post("/classify", json={"code": "24.46"})
    assert response.status_code == 200
    data = response.json()
    assert data["input"] == "24.46"
    assert data["result"]["codigo_iaf"] is not None
    print("PASS")

def test_advanced_search_post():
    print("Testing POST /classify with query (Advanced)...")
    payload = {
        "query": "construcción de edificios",
        "actividades_reales": "albañilería",
        "procesos_criticos": "trabajo en altura"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    # Check for risks
    assert "riesgos" in data["results"][0]
    print("PASS")

def test_search_get():
    print("Testing GET /search?q=construcción...")
    response = client.get("/search?q=construcción")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    print("PASS")

if __name__ == "__main__":
    try:
        test_legacy_get()
        test_legacy_post()
        test_advanced_search_post()
        test_search_get()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nFAILED: {e}")
        exit(1)
