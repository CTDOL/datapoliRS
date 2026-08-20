document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const cargoSelect = document.getElementById("cargoSelect");
    const autocompleteDropdown = document.getElementById("autocompleteDropdown");
    const loader = document.getElementById("loader");
    const errorMessage = document.getElementById("errorMessage");
    const resultContainer = document.getElementById("resultContainer");

    const metricTotalVotes = document.getElementById("metricTotalVotes");
    const metricTotalMunicipios = document.getElementById("metricTotalMunicipios");
    const metricTopReduto = document.getElementById("metricTopReduto");
    const topRankingBody = document.getElementById("topRankingBody");

    let mapInstance = null;
    let geojsonData = null;
    let debounceTimer = null;

    const formatNumber = (num) => new Intl.NumberFormat('pt-BR').format(num);

    // 1. Inicialização do Mapa Leaflet
    const initMap = () => {
        if (!mapInstance) {
            mapInstance = L.map('map', { zoomControl: true }).setView([-30.033, -53.23], 6);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap contributors &copy; CARTO &copy; datapoliRS',
                subdomains: 'abcd',
                maxZoom: 18
            }).addTo(mapInstance);
        }
        setTimeout(() => mapInstance.invalidateSize(), 300);
    };

    // 2. Busca de Candidatos (Autocomplete e Submit)
    const handleAutocomplete = async () => {
        const query = searchInput.value.trim();
        if (query.length < 2) {
            autocompleteDropdown.classList.add("hidden");
            autocompleteDropdown.innerHTML = "";
            return;
        }

        const cargoVal = cargoSelect.value;
        const cargoParam = cargoVal ? `&cd_cargo=${cargoVal}` : "";
        const anoVal = document.getElementById("anoSelect").value;
        const anoParam = `&ano=${anoVal}`;

        try {
            const res = await fetch(`/api/v1/candidatos?termo=${encodeURIComponent(query)}${cargoParam}${anoParam}&limite=8`);
            if (!res.ok) return;
            const candidates = await res.json();

            if (candidates.length === 0) {
                autocompleteDropdown.classList.add("hidden");
                return;
            }

            autocompleteDropdown.innerHTML = candidates.map(c => `
                <div class="dropdown-item" data-sq="${c.sq_candidato}">
                    <div class="dropdown-title">
                        <strong>${c.nm_urna_candidato}</strong> (${c.nr_candidato})
                    </div>
                    <div class="dropdown-subtitle">
                        ${c.ds_cargo} • ${c.sg_partido}
                    </div>
                </div>
            `).join("");

            autocompleteDropdown.classList.remove("hidden");

            // Eventos de clique nas opções
            document.querySelectorAll(".dropdown-item").forEach(item => {
                item.addEventListener("click", () => {
                    const sq = item.getAttribute("data-sq");
                    autocompleteDropdown.classList.add("hidden");
                    loadCandidateBySq(sq);
                });
            });

        } catch (err) {
            console.error("Erro no autocomplete:", err);
        }
    };

    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        autocompleteDropdown.classList.add("hidden");
        errorMessage.classList.add("hidden");
        resultContainer.classList.add("hidden");
        loader.classList.remove("hidden");

        const cargoVal = cargoSelect.value;
        const cargoParam = cargoVal ? `cd_cargo=${cargoVal}&` : "";
        const anoVal = document.getElementById("anoSelect").value;
        const anoParam = `ano=${anoVal}`;

        try {
            // Se for número puro, busca direto por número
            if (!isNaN(query) && parseInt(query) > 0) {
                const res = await fetch(`/api/v1/votacao/numero/${query}?${cargoParam}${anoParam}`);
                if (!res.ok) throw new Error("Candidato não localizado para o número informado.");
                const votingData = await res.json();
                renderVotingDashboard(votingData);
                return;
            }

            // Senão, busca por nome na API
            const res = await fetch(`/api/v1/candidatos?termo=${encodeURIComponent(query)}&${cargoParam}${anoParam}&limite=1`);
            if (!res.ok) throw new Error("Erro ao buscar dados no servidor.");
            const candidates = await res.json();

            if (!candidates || candidates.length === 0) {
                throw new Error(`Nenhum candidato encontrado com o termo '${query}'.`);
            }

            await loadCandidateBySq(candidates[0].sq_candidato);

        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.classList.remove("hidden");
        } finally {
            loader.classList.add("hidden");
        }
    };

    const loadCandidateBySq = async (sqCandidato) => {
        errorMessage.classList.add("hidden");
        resultContainer.classList.add("hidden");
        loader.classList.remove("hidden");

        try {
            const res = await fetch(`/api/v1/votacao/candidatos/${sqCandidato}/municipios`);
            if (!res.ok) throw new Error("Não foi possível carregar a votação deste candidato.");
            const votingData = await res.json();
            renderVotingDashboard(votingData);
        } catch (err) {
            errorMessage.textContent = err.message;
            errorMessage.classList.remove("hidden");
        } finally {
            loader.classList.add("hidden");
        }
    };

    // 3. Renderização dos Resultados no Dashboard
    const renderVotingDashboard = (data) => {
        // Dados do Candidato
        document.getElementById("candidateUrnaName").textContent = data.nm_urna_candidato;
        document.getElementById("candidateFullName").textContent = data.nm_candidato;
        document.getElementById("candidateParty").textContent = data.sg_partido;
        document.getElementById("candidateNumber").textContent = data.nr_candidato;
        document.getElementById("candidateCargo").textContent = data.ds_cargo;
        
        document.getElementById("electionBadge").textContent = `Eleições ${document.getElementById("anoSelect").value}`;

        // Foto oficial com proxy resiliente e cache
        const photoEl = document.getElementById("candidatePhoto");
        photoEl.src = `/api/v1/candidatos/${data.sq_candidato}/foto`;
        photoEl.onerror = () => {
            photoEl.src = "https://via.placeholder.com/120x120?text=Sem+Foto";
        };

        // Métricas
        metricTotalVotes.textContent = formatNumber(data.total_votos_estado);
        
        // Filtra municípios onde o candidato realmente teve votos
        const municipiosComVoto = data.distribuicao_municipios.filter(m => m.votos > 0).length;
        metricTotalMunicipios.textContent = `${municipiosComVoto} / 497`;

        const topReduto = data.distribuicao_municipios[0];
        if (topReduto) {
            metricTopReduto.textContent = `${topReduto.nm_municipio} (${topReduto.percentual_total_candidato}%)`;
        } else {
            metricTopReduto.textContent = "Nenhum voto";
        }

        // Tabela Top 10 Redutos
        const top10 = data.distribuicao_municipios.slice(0, 10);
        topRankingBody.innerHTML = top10.map((mun, idx) => `
            <tr>
                <td><strong>#${idx + 1}</strong></td>
                <td>${mun.nm_municipio}</td>
                <td><strong>${formatNumber(mun.votos)}</strong></td>
                <td><span class="badge-percent">${mun.percentual_total_candidato}%</span></td>
            </tr>
        `).join("");

        resultContainer.classList.remove("hidden");

        // Desenhar Mapa Coroplético PostGIS
        drawChoroplethMap(data);
    };

    // 4. Renderização do Mapa Coroplético
    const drawChoroplethMap = async (votingData) => {
        initMap();

        try {
            // Carregar GeoJSON via PostGIS Endpoint
            if (!geojsonData) {
                const geoRes = await fetch('/api/v1/geo/municipios');
                if (geoRes.ok) {
                    geojsonData = await geoRes.json();
                } else {
                    // Fallback estático
                    const fallbackRes = await fetch('/static/rs_municipios.json');
                    geojsonData = await fallbackRes.json();
                }
            }

            // Mapa de votos indexado por código TSE e por nome normalizado
            const votesByTse = {};
            const votesByName = {};
            let maxVotes = 0;

            votingData.distribuicao_municipios.forEach(item => {
                if (item.cd_tse_municipio) votesByTse[item.cd_tse_municipio] = item.votos;
                if (item.nm_municipio) votesByName[item.nm_municipio.trim().toUpperCase()] = item.votos;
                if (item.votos > maxVotes) maxVotes = item.votos;
            });

            // Escala de cores profissional (Blue Spectrum)
            const getColor = (v) => {
                if (v === 0 || !v) return '#f1f5f9';
                if (v > maxVotes * 0.75) return '#084081';
                if (v > maxVotes * 0.50) return '#0868ac';
                if (v > maxVotes * 0.25) return '#2b8cbe';
                if (v > maxVotes * 0.10) return '#4eb3d3';
                if (v > maxVotes * 0.02) return '#7bccc4';
                return '#ccebc5';
            };

            const style = (feature) => {
                const props = feature.properties || {};
                const tseCode = props.cd_tse;
                const name = (props.name || "").trim().toUpperCase();
                const votes = (tseCode && votesByTse[tseCode] !== undefined) ? votesByTse[tseCode] : (votesByName[name] || 0);

                return {
                    fillColor: getColor(votes),
                    weight: 1,
                    opacity: 1,
                    color: '#ffffff',
                    fillOpacity: 0.8
                };
            };

            // Limpar camadas anteriores
            mapInstance.eachLayer(layer => {
                if (layer.toGeoJSON) {
                    mapInstance.removeLayer(layer);
                }
            });

            // Adicionar Camada PostGIS GeoJSON com Tooltip
            L.geoJson(geojsonData, {
                style: style,
                onEachFeature: (feature, layer) => {
                    const props = feature.properties || {};
                    const munName = props.name || "Município";
                    const tseCode = props.cd_tse;
                    const votes = (tseCode && votesByTse[tseCode] !== undefined) ? votesByTse[tseCode] : (votesByName[munName.toUpperCase()] || 0);
                    const pct = votingData.total_votos_estado > 0 ? ((votes / votingData.total_votos_estado) * 100).toFixed(2) : 0;

                    layer.bindTooltip(`
                        <div style="font-family: Inter, sans-serif;">
                            <strong style="font-size: 13px;">${munName}</strong><br/>
                            Votos: <strong>${formatNumber(votes)}</strong><br/>
                            Concentração: <strong>${pct}%</strong>
                        </div>
                    `);
                }
            }).addTo(mapInstance);

        } catch (err) {
            console.error("Erro ao desenhar mapa PostGIS:", err);
        }
    };

    // Eventos
    searchBtn.addEventListener("click", performSearch);
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") performSearch();
    });

    searchInput.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(handleAutocomplete, 300);
    });

    cargoSelect.addEventListener("change", () => {
        if (searchInput.value.trim().length >= 2) {
            handleAutocomplete();
        }
    });

    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !autocompleteDropdown.contains(e.target)) {
            autocompleteDropdown.classList.add("hidden");
        }
    });
});
