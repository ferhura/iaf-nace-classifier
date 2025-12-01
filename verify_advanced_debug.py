from iaf_nace_classifier.search import buscar_actividad

def verify_advanced_features_debug():
    print("\n--- Test 2 Debug: Advanced Query ---")
    res2 = buscar_actividad(
        query="desarrollo de software", 
        actividades_reales="programación de PLCs", 
        procesos_criticos="control de maquinaria industrial",
        top_n=5
    )
    for r in res2['results']:
        print(f"[{r['codigo_nace']}] {r['relevancia']:.1f} - {r['descripcion_nace'][:60]}...")

if __name__ == "__main__":
    verify_advanced_features_debug()
