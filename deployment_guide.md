# Guía de Despliegue (Deployment)

Esta guía explica cómo subir y ejecutar tu aplicación **IAF/NACE Classifier** en la nube para que sea accesible públicamente.

## Opción 1: Replit (Recomendado por ti)

Replit es excelente para prototipos rápidos y edición de código en el navegador.

1.  **Crear cuenta:** Ve a [replit.com](https://replit.com) y crea una cuenta.
2.  **Nuevo Repl:** Haz clic en "+ Create Repl" y selecciona la plantilla **"Python"**.
3.  **Subir archivos:**
    *   Arrastra y suelta todos los archivos de tu carpeta `iaf-nace-classifier` al panel de archivos de Replit.
    *   Asegúrate de incluir:
        *   La carpeta `iaf_nace_classifier/` (con todo su contenido).
        *   La carpeta `static/`.
        *   El archivo `requirements.txt` (que acabo de crear).
        *   El archivo `iaf_nace_mapeo_expandido.json` (dentro de `iaf_nace_classifier/data/`).
4.  **Configurar el arranque:**
    *   En el archivo `.replit` (si existe) o en el botón "Run", configura el comando de ejecución.
    *   Replit suele detectar el archivo `main.py`. Como no tenemos uno en la raíz, crea un archivo llamado `main.py` en la raíz con este contenido:
        ```python
        import uvicorn
        from iaf_nace_classifier.api import app

        if __name__ == "__main__":
            uvicorn.run(app, host="0.0.0.0", port=8080)
        ```
5.  **Instalar dependencias:**
    *   Ve a la herramienta "Shell" (terminal) en Replit y ejecuta:
        ```bash
        pip install -r requirements.txt
        ```
    *   O simplemente dale al botón "Run", Replit intentará instalar los paquetes si detecta los imports.
6.  **Ejecutar:** Haz clic en el botón verde **"Run"**.
    *   Verás una ventana "Webview" con tu aplicación funcionando.
    *   La URL de esa ventana (ej. `https://tu-proyecto.tu-usuario.repl.co`) es tu API pública.

## Opción 2: Render (Más profesional y gratuito)

Render es una plataforma muy estable para desplegar servicios web Python.

1.  **GitHub:** Sube tu código a un repositorio de GitHub (si no lo has hecho ya).
2.  **Crear Web Service:**
    *   Ve a [render.com](https://render.com) y crea una cuenta.
    *   Haz clic en "New +" -> "Web Service".
    *   Conecta tu repositorio de GitHub.
3.  **Configuración:**
    *   **Name:** (Elige un nombre, ej. `iaf-nace-search`)
    *   **Runtime:** Python 3
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `uvicorn iaf_nace_classifier.api:app --host 0.0.0.0 --port $PORT`
4.  **Desplegar:** Haz clic en "Create Web Service".
    *   Render instalará las dependencias y lanzará la app.
    *   Te dará una URL (ej. `https://iaf-nace-search.onrender.com`).

## Integración con WordPress

Una vez desplegado (en Replit o Render), obtendrás una **URL pública** (ej. `https://mi-app.onrender.com`).

Para integrarlo en tu WordPress:
1.  Abre el archivo `wordpress_integration.html` que te preparé.
2.  Busca la línea:
    ```javascript
    const API_URL = 'http://localhost:8000'; // CAMBIAR ESTO POR TU URL DE REPLIT/RENDER
    ```
3.  Cámbiala por tu nueva URL pública:
    ```javascript
    const API_URL = 'https://tu-proyecto.tu-usuario.repl.co'; // Ejemplo Replit
    // O
    const API_URL = 'https://iaf-nace-search.onrender.com'; // Ejemplo Render
    ```
4.  Copia y pega el código en tu WordPress.
