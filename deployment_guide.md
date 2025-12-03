# Guía de Despliegue (Deployment)

Esta guía explica cómo subir y ejecutar tu aplicación **IAF/NACE Classifier** en la nube de forma fácil y gratuita (o de bajo costo).

He preparado tu proyecto para que funcione automáticamente en **Render** (recomendado) o **Railway**.

## Opción 1: Render (Recomendado - Capa Gratuita)

Render es excelente, fácil de usar y tiene una capa gratuita generosa para servicios web.

1.  **GitHub:** Asegúrate de subir los nuevos archivos (`Procfile`, `Dockerfile`, `runtime.txt`) a tu repositorio de GitHub.
2.  **Crear Web Service:**
    *   Ve a [render.com](https://render.com) y crea una cuenta.
    *   Haz clic en **"New +"** -> **"Web Service"**.
    *   Conecta tu repositorio de GitHub `iaf-nace-classifier`.
3.  **Configuración Automática:**
    *   Render detectará automáticamente el entorno Python.
    *   **Name:** Elige un nombre (ej. `iaf-nace-classifier`).
    *   **Region:** La que prefieras (ej. Ohio o Frankfurt).
    *   **Branch:** `main` (o la rama donde tengas el código).
    *   **Root Directory:** Déjalo en blanco.
    *   **Runtime:** `Python 3`.
    *   **Build Command:** `pip install -r requirements.txt` (Render debería detectarlo).
    *   **Start Command:** `uvicorn iaf_nace_classifier.api:app --host 0.0.0.0 --port $PORT` (Render leerá esto del `Procfile` automáticamente, pero si te pregunta, es este).
4.  **Desplegar:**
    *   Selecciona el plan **"Free"**.
    *   Haz clic en **"Create Web Service"**.
5.  **Listo:**
    *   Espera unos minutos a que termine el "Build" y el "Deploy".
    *   Verás una URL arriba a la izquierda (ej. `https://iaf-nace-classifier.onrender.com`). Esa es tu API pública.

## Opción 2: Railway (Alternativa muy robusta)

Railway es otra excelente opción, a veces más rápida que Render, pero su capa gratuita es limitada en tiempo de uso (créditos de prueba).

1.  **GitHub:** Sube tus cambios a GitHub.
2.  **Crear Proyecto:**
    *   Ve a [railway.app](https://railway.app) y haz login con GitHub.
    *   Haz clic en **"New Project"** -> **"Deploy from GitHub repo"**.
    *   Selecciona tu repositorio `iaf-nace-classifier`.
3.  **Despliegue Automático:**
    *   Railway detectará el `Dockerfile` o el `Procfile` y desplegará automáticamente.
    *   Si usa el `Dockerfile`, construirá la imagen y la lanzará.
4.  **Generar Dominio:**
    *   Una vez desplegado, ve a la pestaña **"Settings"** del servicio.
    *   En la sección **"Networking"**, haz clic en **"Generate Domain"**.
    *   Obtendrás una URL pública (ej. `iaf-nace-classifier-production.up.railway.app`).

## Integración con WordPress

Una vez tengas tu URL pública (de Render o Railway):

1.  Abre el archivo `wordpress_integration.html` en tu ordenador.
2.  Busca la línea:
    ```javascript
    const API_URL = 'http://localhost:8000';
    ```
3.  Cámbiala por tu nueva URL pública (sin la barra al final):
    ```javascript
    const API_URL = 'https://iaf-nace-classifier.onrender.com';
    ```
4.  Copia todo el código del archivo y pégalo en un bloque "HTML Personalizado" en tu página de WordPress.
