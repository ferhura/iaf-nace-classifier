const searchInput = document.getElementById('searchInput');
const resultsContainer = document.getElementById('resultsContainer');
const loadingSpinner = document.getElementById('loadingSpinner');

let debounceTimer;

searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();

    clearTimeout(debounceTimer);

    if (query.length < 2) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <p>Escribe al menos 2 caracteres para buscar...</p>
            </div>
        `;
        return;
    }

    loadingSpinner.classList.remove('hidden');

    debounceTimer = setTimeout(() => {
        fetchResults(query);
    }, 400); // 400ms debounce
});

async function fetchResults(query) {
    try {
        const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Error en la búsqueda');

        const data = await response.json();
        // Support both old list format (just in case) and new dict format
        const results = Array.isArray(data) ? data : (data.results || []);
        const excluded = data.excluded || [];

        renderResults(results, excluded, query);
    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = `
            <div class="empty-state" style="color: #ef4444;">
                <p>Ocurrió un error al buscar. Inténtalo de nuevo.</p>
            </div>
        `;
    } finally {
        loadingSpinner.classList.add('hidden');
    }
}

function renderResults(results, excluded, query) {
    if ((!results || results.length === 0) && (!excluded || excluded.length === 0)) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <p>No se encontraron resultados para "<strong>${escapeHtml(query)}</strong>"</p>
            </div>
        `;
        return;
    }

    let html = '';

    // 1. Render Valid Results
    if (results && results.length > 0) {
        // Agrupar resultados por código IAF preservando el orden de aparición
        const groups = [];
        const groupsMap = new Map();

        results.forEach(item => {
            if (!groupsMap.has(item.codigo_iaf)) {
                const group = {
                    iaf_code: item.codigo_iaf,
                    iaf_name: item.nombre_iaf,
                    items: []
                };
                groupsMap.set(item.codigo_iaf, group);
                groups.push(group);
            }
            groupsMap.get(item.codigo_iaf).items.push(item);
        });

        html += groups.map(group => {
            const itemsHtml = group.items.map(item => {
                const percentage = Math.min(100, Math.max(10, (item.relevancia / 350) * 100));
                const highlightedDesc = highlightTerms(item.descripcion_nace, query);

                // Exclusions within valid results (warnings)
                let exclusionHtml = '';
                // Use full description to find exclusions, even if truncated in display
                const fullDesc = item.descripcion_completa || item.descripcion_nace;
                const lowerFullDesc = fullDesc.toLowerCase();

                if (lowerFullDesc.includes('excepto') || lowerFullDesc.includes('no comprende')) {
                    let exclusionText = '';
                    if (lowerFullDesc.includes('excepto')) {
                        exclusionText = fullDesc.substring(lowerFullDesc.indexOf('excepto'));
                    } else if (lowerFullDesc.includes('no comprende')) {
                        exclusionText = fullDesc.substring(lowerFullDesc.indexOf('no comprende'));
                    }

                    // Clean up: Remove leading "Esta clase " if present before "no comprende"
                    // (The substring above starts at "no comprende", so this is just for safety/formatting)

                    if (exclusionText.length > 200) exclusionText = exclusionText.substring(0, 200) + '...';

                    exclusionHtml = `
                        <div class="exclusion-box">
                            <strong>⚠️ Nota:</strong> ${escapeHtml(exclusionText)}
                        </div>
                    `;
                }

                return `
                    <div class="nace-item">
                        <div class="nace-header">
                            <span class="nace-code-large">NACE ${item.codigo_nace}</span>
                            <div class="score-bar-container" title="Relevancia: ${item.relevancia.toFixed(1)}">
                                <div class="score-bar" style="width: ${percentage}%"></div>
                            </div>
                        </div>
                        <p class="description">${highlightedDesc}</p>
                        ${exclusionHtml}
                    </div>
                `;
            }).join('');

            return `
                <div class="iaf-group">
                    <div class="iaf-info">
                        <span class="badge-iaf">IAF ${group.iaf_code}</span>
                        <h3>${escapeHtml(group.iaf_name)}</h3>
                    </div>
                    <div class="nace-list">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        }).join('');
    }

    // 2. Render Excluded Results
    if (excluded && excluded.length > 0) {
        html += `
            <div class="excluded-section">
                <h3 class="excluded-title">Sectores Analizados pero Excluidos</h3>
                <p class="excluded-subtitle">Estos sectores coinciden con tu búsqueda pero contienen exclusiones específicas.</p>
                <div class="excluded-grid">
        `;

        html += excluded.map(item => {
            return `
                <div class="card excluded-card">
                    <div class="card-header">
                        <span class="badge-iaf badge-excluded">IAF ${item.codigo_iaf}</span>
                        <span class="nace-code">NACE ${item.codigo_nace}</span>
                    </div>
                    <div class="card-body">
                        <p class="description" style="margin-bottom: 0.5rem;">${escapeHtml(item.descripcion_nace)}</p>
                        <div class="exclusion-reason">
                            <strong>⛔ Excluido por:</strong> "${escapeHtml(item.razon_exclusion)}"
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        html += `
                </div>
            </div>
        `;
    }

    resultsContainer.innerHTML = html;
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function highlightTerms(text, query) {
    if (!query || !text) return text;

    const terms = query.split(/\s+/).filter(t => t.length > 2);
    if (terms.length === 0) return text;

    let highlighted = text;
    // Ordenar términos por longitud descendente para evitar reemplazos anidados incorrectos
    terms.sort((a, b) => b.length - a.length);

    terms.forEach(term => {
        // Regex simple para case-insensitive replace
        const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');
        highlighted = highlighted.replace(regex, '<span class="highlight">$1</span>');
    });

    return highlighted;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
