# Project Overview

This project provides a tool to map NACE (Nomenclature of Economic Activities) codes to IAF (International Accreditation Forum) sectors. It includes a data extraction pipeline to process a PDF file containing the mappings, a CLI to classify NACE codes, a Python API for programmatic use, and a web server to expose the functionality as a REST API.

The core of the project is a Python script that extracts the mappings from a PDF document, normalizes the data, and saves it as a JSON file. This JSON file is then used by the classifier to map NACE codes to IAF sectors.

## Key Technologies

*   **Python:** The entire project is written in Python.
*   **PyMuPDF (fitz):** Used for extracting text and data from the PDF file.
*   **FastAPI:** Used to create the web server that exposes the classification functionality as a REST API.
*   **Uvicorn:** Used as the ASGI server for the FastAPI application.

## Project Structure

The project is organized into the following key files and directories:

*   `extract_iaf_nace.py`: The script responsible for extracting the NACE-IAF mappings from the PDF file and generating the `iaf_nace_mapeo_expandido.json` file.
*   `iaf_nace_mapeo_expandido.json`: The JSON file containing the processed and expanded NACE-IAF mappings.
*   `iaf_nace_classifier/`: A Python package containing the core classification logic.
    *   `mapping.py`: Contains the functions for loading the mapping data and classifying NACE codes.
    *   `cli.py`: Implements the command-line interface for the classifier.
*   `api_server.py`: A FastAPI application that exposes the classifier as a REST API.
*   `README.md`: Provides a detailed overview of the project, including installation instructions and usage examples.

# Building and Running

## Installation

The project requires Python 3.10 or higher. The core classification functionality does not require any external dependencies.

To regenerate the `iaf_nace_mapeo_expandido.json` file from the PDF, you need to install `PyMuPDF`:

```bash
pip install PyMuPDF
```

To run the web server, you need to install `fastapi` and `uvicorn`:

```bash
pip install fastapi uvicorn
```

## Running the Extractor

To regenerate the `iaf_nace_mapeo_expandido.json` file, run the following command:

```bash
python extract_iaf_nace.py
```

This will process the `Codigo_NACE_sectoresema.pdf` file and create the `iaf_nace_mapeo_expandido.json` file.

## Running the CLI

To classify a NACE code using the CLI, use the following command:

```bash
python -m iaf_nace_classifier.cli <NACE_CODE>
```

For example:

```bash
python -m iaf_nace_classifier.cli 24.46
```

## Running the API Server

To start the web server, run the following command:

```bash
uvicorn api_server:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can then use `curl` or any other HTTP client to send requests to the `/classify` endpoint.

# Development Conventions

The code is well-structured and follows standard Python conventions. The use of type hints and docstrings makes the code easy to understand and maintain. The project is organized into a package, which makes it easy to import and use in other projects.
