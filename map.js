/**
 * VetBooking - Integração com Mapa
 * Utilizando Leaflet com OpenStreetMap
 */

document.addEventListener('DOMContentLoaded', function() {
    // Verifica se o elemento do mapa existe na página
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;
    
    // Inicializa o mapa
    const map = L.map('map-container').setView([-25.4284, -49.2733], 12); // Coordenadas de Curitiba como padrão
    
    // Adiciona a camada de tiles do OpenStreetMap
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Função para obter a localização atual do usuário
    function obterLocalizacaoAtual() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    // Centraliza o mapa na localização do usuário
                    map.setView([lat, lng], 15);
                    
                    // Adiciona um marcador na localização do usuário
                    const marcadorUsuario = L.marker([lat, lng]).addTo(map);
                    marcadorUsuario.bindPopup('Sua localização atual').openPopup();
                    
                    // Busca endereço baseado nas coordenadas (geocodificação reversa)
                    buscarEnderecoPorCoordenadas(lat, lng);
                },
                function(error) {
                    console.error('Erro ao obter localização:', error);
                    // Em caso de erro, mantém a visualização padrão
                }
            );
        }
    }
    
    // Função para buscar endereço a partir de coordenadas usando a API Nominatim do OpenStreetMap
    function buscarEnderecoPorCoordenadas(lat, lng) {
        const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data && data.address) {
                    // Extrai informações do endereço
                    const cidade = data.address.city || data.address.town || data.address.village || '';
                    const estado = data.address.state || '';
                    
                    // Atualiza o campo de localidade no formulário de busca
                    const selectLocation = document.getElementById('Location');
                    if (selectLocation) {
                        // Verifica se a cidade existe nas opções
                        let cidadeEncontrada = false;
                        for (let i = 0; i < selectLocation.options.length; i++) {
                            if (selectLocation.options[i].text === cidade) {
                                selectLocation.selectedIndex = i;
                                cidadeEncontrada = true;
                                break;
                            }
                        }
                        
                        // Se não encontrou a cidade nas opções, adiciona uma nova opção
                        if (!cidadeEncontrada && cidade) {
                            const novaOpcao = document.createElement('option');
                            novaOpcao.value = cidade;
                            novaOpcao.text = cidade;
                            selectLocation.add(novaOpcao);
                            selectLocation.value = cidade;
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Erro ao buscar endereço:', error);
            });
    }
    
    // Botão para obter localização atual
    const btnLocalizacao = document.createElement('button');
    btnLocalizacao.type = 'button';
    btnLocalizacao.className = 'location-button';
    btnLocalizacao.innerHTML = '<i class="fas fa-map-marker-alt"></i> Usar minha localização';
    btnLocalizacao.addEventListener('click', obterLocalizacaoAtual);
    
    // Adiciona o botão após o select de localidade
    const locationSelect = document.getElementById('Location');
    if (locationSelect && locationSelect.parentNode) {
        locationSelect.parentNode.appendChild(btnLocalizacao);
    }
    
    // Adiciona marcadores para as clínicas em destaque
    const locaisDestaque = [
        { nome: 'Clínica PetCare', lat: -25.4284, lng: -49.2733, especialidade: 'Consultas e Exames' },
        { nome: 'Hospital São Francisco', lat: -25.5284, lng: -49.2033, especialidade: 'Cirurgias e Internação' },
        { nome: 'Centro Vida Animal', lat: -25.4684, lng: -49.3033, especialidade: 'Vacinação e Pet Shop' }
    ];
    
    locaisDestaque.forEach(local => {
        const marker = L.marker([local.lat, local.lng]).addTo(map);
        marker.bindPopup(`<strong>${local.nome}</strong><br>Especialidade: ${local.especialidade}`);
    });
});