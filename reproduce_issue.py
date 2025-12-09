
import sys
import logging
from iaf_nace_classifier.search import buscar_actividad, normalizar_texto, calcular_relevancia, load_mapping

# Setup logging to see what's happening if needed
logging.basicConfig(level=logging.DEBUG)

def reproduce():
    query = "Prestación de servicios de diagnóstico y tratamiento para trastornos del sueño y neurorehabilitación"
    print(f"Query: {query}")
    
    # Load mapping
    mapping = load_mapping()
    
    # Run search
    result = buscar_actividad(query, mapping=mapping, top_n=20)
    
    print("\n--- Top Results ---")
    for res in result['results']:
        print(f"I: {res['codigo_iaf']} | N: {res['codigo_nace']} | Score: {res['relevancia']:.2f}")
        print(f"   Desc: {res['descripcion_nace'][:100]}...")
        
    # Inspect descriptions for key sectors
    print("\n--- Target NACE Descriptions ---")
    
    target_codes = ['84.2', '86.10', '86.21', '86.22', '86.90']
    
    for sector in mapping:
        for desc_obj in sector.get('descripcion_nace', []):
            code = desc_obj.get('codigo')
            if code in target_codes:
                print(f"\nCode: {code}")
                print(f"Desc: {desc_obj.get('descripcion')}")

if __name__ == "__main__":
    reproduce()
