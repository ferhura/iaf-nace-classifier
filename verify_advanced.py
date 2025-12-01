from iaf_nace_classifier.search import buscar_actividad

def verify_advanced_features():
    print("--- Test 1: Basic Query (Construction) ---")
    res1 = buscar_actividad("construcción de edificios", top_n=1)
    if res1['results']:
        r = res1['results'][0]
        print(f"Code: {r['codigo_nace']}")
        print(f"Risks: {r.get('riesgos', 'No risks found')}")
    
    print("\n--- Test 2: Advanced Query (Software + Manufacturing Process) ---")
    # Query implies software, but process implies manufacturing.
    # This should ideally still be software if query is strong, or maybe manufacturing if process dominates.
    # Let's see if risks are attached.
    res2 = buscar_actividad(
        query="desarrollo de software", 
        actividades_reales="programación de PLCs", 
        procesos_criticos="control de maquinaria industrial",
        top_n=1
    )
    if res2['results']:
        r = res2['results'][0]
        print(f"Code: {r['codigo_nace']}")
        print(f"Risks: {r.get('riesgos', 'No risks found')}")

if __name__ == "__main__":
    verify_advanced_features()
