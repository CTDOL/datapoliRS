document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const loader = document.getElementById("loader");
    const errorMessage = document.getElementById("errorMessage");
    const resultContainer = document.getElementById("resultContainer");

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    };

    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        // Reset UI
        errorMessage.classList.add("hidden");
        resultContainer.classList.add("hidden");
        loader.classList.remove("hidden");

        try {
            const response = await fetch(`/api/v1/candidatas/rs?nome=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error("Candidata não encontrada.");
                }
                throw new Error("Erro ao buscar dados no servidor.");
            }

            const data = await response.json();
            renderCandidate(data);
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.classList.remove("hidden");
        } finally {
            loader.classList.add("hidden");
        }
    };

    const renderCandidate = (data) => {
        // Imagem
        const photoEl = document.getElementById("candidatePhoto");
        photoEl.src = data.foto_url || "https://via.placeholder.com/120?text=Sem+Foto";
        
        // Info Básica
        document.getElementById("candidateUrnaName").textContent = data.nome_urna;
        document.getElementById("candidateFullName").textContent = data.nome_completo;
        
        // Tags
        document.getElementById("candidateParty").textContent = data.partido;
        document.getElementById("candidateNumber").textContent = data.numero_urna;
        document.getElementById("candidateStatus").textContent = data.situacao_candidatura;
        
        // Bens Totais
        document.getElementById("totalAssets").textContent = formatCurrency(data.total_bens);
        
        // Lista de Bens
        const assetsListEl = document.getElementById("assetsList");
        assetsListEl.innerHTML = "";
        
        if (data.lista_bens && data.lista_bens.length > 0) {
            data.lista_bens.forEach(bem => {
                const item = document.createElement("div");
                item.className = "asset-item";
                item.innerHTML = `
                    <div>
                        <span class="asset-desc">${bem.descricao || bem.tipo}</span>
                        <span class="asset-type">${bem.tipo || 'Outros'}</span>
                    </div>
                    <span class="asset-val">${formatCurrency(bem.valor)}</span>
                `;
                assetsListEl.appendChild(item);
            });
        } else {
            assetsListEl.innerHTML = "<p style='color: var(--text-muted)'>Nenhum bem declarado.</p>";
        }

        // Fetch votes and draw map
        fetchAndDrawMap(data.numero_urna);

        // Show results
        resultContainer.classList.remove("hidden");
    };

    let mapInstance = null;
    let geojsonData = null;

    const initMap = () => {
        if (!mapInstance) {
            mapInstance = L.map('map').setView([-30.033, -51.23], 6);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 20
            }).addTo(mapInstance);
        }
    };

    const fetchAndDrawMap = async (numeroUrna) => {
        initMap();
        
        try {
            // Load GeoJSON if not loaded
            if (!geojsonData) {
                const geoRes = await fetch('/static/rs_municipios.json');
                geojsonData = await geoRes.json();
            }

            // Load Votes
            const votesRes = await fetch(`/api/v1/candidatas/${numeroUrna}/votos`);
            if (!votesRes.ok) {
                console.log("No votes found for this candidate");
                return;
            }
            const votesData = await votesRes.json();
            
            // Create a map of municipality name to votes
            const votesMap = {};
            let maxVotes = 0;
            votesData.forEach(item => {
                // Normalize names to match GeoJSON (uppercase, remove accents if needed)
                const name = item.municipio.trim().toUpperCase();
                votesMap[name] = item.votos;
                if (item.votos > maxVotes) maxVotes = item.votos;
            });

            // Color scale function
            const getColor = (d) => {
                return d > maxVotes * 0.8 ? '#08519c' :
                       d > maxVotes * 0.5 ? '#3182bd' :
                       d > maxVotes * 0.2 ? '#6baed6' :
                       d > 0              ? '#bdd7e7' :
                                            '#f0f0f0'; // zero votes
            };

            const style = (feature) => {
                const munName = feature.properties.name.toUpperCase();
                const votes = votesMap[munName] || 0;
                return {
                    fillColor: getColor(votes),
                    weight: 1,
                    opacity: 1,
                    color: 'white',
                    fillOpacity: 0.7
                };
            };

            // Clear existing layers
            mapInstance.eachLayer((layer) => {
                if (!!layer.toGeoJSON) {
                    mapInstance.removeLayer(layer);
                }
            });

            // Add GeoJSON
            L.geoJson(geojsonData, {
                style: style,
                onEachFeature: (feature, layer) => {
                    const munName = feature.properties.name;
                    const votes = votesMap[munName.toUpperCase()] || 0;
                    layer.bindTooltip(`<b>${munName}</b><br/>Votos: ${votes}`);
                }
            }).addTo(mapInstance);

        } catch (error) {
            console.error("Error drawing map:", error);
        }
    };

    // Events
    searchBtn.addEventListener("click", performSearch);
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            performSearch();
        }
    });
});
