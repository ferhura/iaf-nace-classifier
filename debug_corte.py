from iaf_nace_classifier.search import buscar_actividad, normalizar_texto, calcular_relevancia
from iaf_nace_classifier.mapping import load_mapping

def debug_corte():
    print("--- Debugging 'corte' search ---")
    
    # 1. Test Normalization
    term = "corte"
    norm = normalizar_texto(term)
    print(f"Normalized term: '{norm}'")
    
    # 2. Test Search Function directly
    print("\nRunning buscar_actividad(actividades_reales='corte')...")
    res = buscar_actividad(query="", actividades_reales="corte", top_n=5)
    
    print(f"Results found: {len(res['results'])}")
    for r in res['results']:
        print(f" - {r['codigo_nace']}: {r['relevancia']} ({r['descripcion_nace'][:50]}...)")
        
    if not res['results']:
        print("\nNo results found. Checking manual relevance calculation...")
        mapping = load_mapping()
        
        # Check if 'corte' appears in any description
        found_in_desc = 0
        for sector in mapping:
            for desc_obj in sector.get('descripcion_nace', []):
                d = desc_obj.get('descripcion', '')
                if 'corte' in d.lower():
                    found_in_desc += 1
                    score, _, _ = calcular_relevancia("corte", d)
                    if score > 0:
                        print(f"Match found in {desc_obj['codigo']}: Score={score}")
                        # print(f"Desc: {d[:100]}...")
        
        print(f"\n'corte' found in {found_in_desc} descriptions.")

if __name__ == "__main__":
    debug_corte()
