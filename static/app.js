const searchInput = document.getElementById('searchInput');
const activitiesInput = document.getElementById('activitiesInput');
const processesInput = document.getElementById('processesInput');
const resultsContainer = document.getElementById('resultsContainer');
const loadingSpinner = document.getElementById('loadingSpinner');
const toggleBtn = document.getElementById('toggleAdvanced');
const advancedInputs = document.getElementById('advancedInputs');

let debounceTimer;

// Toggle advanced inputs
toggleBtn.addEventListener('click', () => {
    advancedInputs.classList.toggle('hidden');
    toggleBtn.textContent = advancedInputs.classList.contains('hidden')
        ? 'Añadir más detalles'
        : 'Ocultar detalles';
});

// Event listeners for all inputs
[searchInput, activitiesInput, processesInput].forEach(input => {
    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(performSearch, 300);
    });
});

async function performSearch() {
    const query = searchInput.value.trim();
    const activities = activitiesInput.value.trim();
    const processes = processesInput.value.trim();

    console.log("Search triggered:", { query, activities, processes });

    if (query.length < 2 && activities.length < 2 && processes.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }

    loadingSpinner.classList.remove('hidden');

    try {
        // Use POST for advanced classification
        const response = await fetch('/classify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                actividades_reales: activities,
                procesos_criticos: processes
            })
        });

        if (!response.ok) throw new Error('Error en la búsqueda');

        const data = await response.json();
        console.log("API Response:", data);

        if (!data || !data.results) {
            throw new Error('Respuesta inválida del servidor');
        }

        renderResults(data);
    } catch (error) {
        console.error('Error details:', error);
        resultsContainer.innerHTML = `<div class="error">
            <p>Ocurrió un error al buscar.</p>
            <small>${error.message}</small>
        </div>`;
    } finally {
        loadingSpinner.classList.add('hidden');
    }
}

function renderResults(data) {
    resultsContainer.innerHTML = '';

    if (data.results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No se encontraron resultados. Intenta con otros términos.</div>';
        return;
    }

    data.results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'result-card';

        // Determinar clase de relevancia
        let relevanceClass = 'low';
        if (item.relevancia >= 80) relevanceClass = 'high';
        else if (item.relevancia >= 50) relevanceClass = 'medium';

        // Procesar exclusiones para mostrar (usando descripción completa)
        let exclusionNote = '';
        if (item.descripcion_completa && item.descripcion_completa.includes('Esta clase no comprende:')) {
            const parts = item.descripcion_completa.split('Esta clase no comprende:');
            if (parts.length > 1) {
                const fullExclusionText = parts[1].trim();
                // Tomar los primeros 200 caracteres de la exclusión para no saturar
                const truncatedText = fullExclusionText.substring(0, 200) + (fullExclusionText.length > 200 ? '...' : '');
                exclusionNote = `<div class="exclusion-note" data-tooltip="${fullExclusionText.replace(/"/g, '&quot;')}">⚠️ <strong>Nota:</strong> No incluye: ${truncatedText}</div>`;
            }
        }

        // Renderizar Riesgos
        let risksHtml = '';
        if (item.riesgos && item.riesgos.length > 0) {
            risksHtml = `
                <div class="risks-container">
                    <h4>⚠️ Riesgos clave del sector:</h4>
                    <ul>
                        ${item.riesgos.map(risk => `<li>${risk}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="result-header">
                <div class="nace-code">${item.codigo_nace}</div>
                <div class="relevance-badge ${relevanceClass}">${Math.min(100, Math.round(item.relevancia))}% Coincidencia</div>
            </div>
            <div class="nace-description">${item.descripcion_nace}</div>
            ${exclusionNote}
            <div class="iaf-info">
                <span class="iaf-label">Sector IAF:</span>
                <span class="iaf-value">${item.codigo_iaf} - ${item.nombre_iaf}</span>
            </div>
            ${risksHtml}
        `;
        resultsContainer.appendChild(card);
    });
}
