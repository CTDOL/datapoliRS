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

        // Show results
        resultContainer.classList.remove("hidden");
    };

    // Events
    searchBtn.addEventListener("click", performSearch);
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            performSearch();
        }
    });
});
