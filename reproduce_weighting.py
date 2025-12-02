from iaf_nace_classifier.search import buscar_actividad

def test_weighting():
    query = "fabrica de calzado"
    activities = "corte"
    processes = "desarrollo de software"
    
    print(f"Query: '{query}'")
    print(f"Activities: '{activities}'")
    print(f"Processes: '{processes}'")
    
    results = buscar_actividad(query, activities, processes, top_n=3)
    
    print("\nTop 3 Results:")
    for i, r in enumerate(results['results']):
        print(f"{i+1}. {r['codigo_nace']} - {r['descripcion_nace']} (Score: {r['relevancia']})")

if __name__ == "__main__":
    test_weighting()
