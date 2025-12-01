from iaf_nace_classifier.mapping import classify_nace, load_mapping

def verify_legacy():
    print("Loading mapping...")
    mapping = load_mapping()
    
    print("Testing code 24.46...")
    res = classify_nace("24.46", mapping)
    assert res is not None
    assert res["codigo_iaf"] is not None
    print(f"Result: {res['codigo_iaf']} - {res['nombre_iaf']}")
    
    print("Testing code 47 (Trade)...")
    res2 = classify_nace("47", mapping)
    assert res2 is not None
    print(f"Result: {res2['codigo_iaf']} - {res2['nombre_iaf']}")
    
    print("Legacy verification PASSED")

if __name__ == "__main__":
    verify_legacy()
