// app/static/js/dashboard_charts.js

function renderCompositeChart(canvasId, pointsData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (window.compositeChartInstance) {
        window.compositeChartInstance.destroy();
    }

    const bimestres = ["B1 (Sep-Oct)", "B2 (Nov-Dic)", "B3 (Ene-Feb)", "B4 (Mar-Abr)", "B5 (May-Jun)"];
    
    // Agrupar por campus
    const seriesByCampus = {
        "Misiones": [79.7, 82.25, 84.4, 86.55, 88.7],
        "Nuevo Sur": [84.6, 86.8, 88.65, 90.5, 92.35],
        "San Agustín": [72.5, 74.9, 76.7, 78.5, 80.3],
        "Global": [78.8, 81.1, 83.06, 85.0, 86.9]
    };

    if (pointsData && Array.isArray(pointsData)) {
        // Extraer valores dinámicos si se especifican
        ["Misiones", "Nuevo Sur", "San Agustín", "Global"].forEach(c => {
            const sub = pointsData.filter(p => p.campus === c);
            if (sub.length >= 5) {
                seriesByCampus[c] = sub.map(p => p.indice);
            }
        });
    }

    window.compositeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: bimestres,
            datasets: [
                {
                    label: 'Global (Ponderado)',
                    data: seriesByCampus["Global"],
                    borderColor: '#0f172a',
                    backgroundColor: '#0f172a',
                    borderWidth: 3,
                    tension: 0.3
                },
                {
                    label: 'Misiones',
                    data: seriesByCampus["Misiones"],
                    borderColor: '#3b82f6',
                    backgroundColor: '#3b82f6',
                    borderWidth: 2,
                    tension: 0.3
                },
                {
                    label: 'Nuevo Sur',
                    data: seriesByCampus["Nuevo Sur"],
                    borderColor: '#10b981',
                    backgroundColor: '#10b981',
                    borderWidth: 2,
                    tension: 0.3
                },
                {
                    label: 'San Agustín',
                    data: seriesByCampus["San Agustín"],
                    borderColor: '#f59e0b',
                    backgroundColor: '#f59e0b',
                    borderWidth: 2,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#94a3b8', font: { family: 'Inter', weight: 600 } }
                }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { min: 60, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}
