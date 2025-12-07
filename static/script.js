document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggling Logic
    const themeBtn = document.getElementById('theme-toggle');
    const html = document.documentElement;
    const icon = themeBtn ? themeBtn.querySelector('i') : null;
    const text = themeBtn ? themeBtn.querySelector('span') : null;

    // Check Local Storage
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!icon) return;
        if (theme === 'dark') {
            icon.className = 'fa-solid fa-sun'; // Show sun to switch to light
            if (text) text.textContent = 'Light Mode';
        } else {
            icon.className = 'fa-solid fa-moon'; // Show moon to switch to dark
            if (text) text.textContent = 'Dark Mode';
        }
    }

    // Modal Logic (Existing functionality preserved)
    const modalBackdrop = document.getElementById('modal-backdrop');
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', (e) => {
            if (e.target === modalBackdrop) {
                closeModal();
            }
        });
    }
});

function viewCandidate(candidateId) {
    const backdrop = document.getElementById('modal-backdrop');
    const content = document.getElementById('modal-content');

    backdrop.classList.remove('hidden');
    content.innerHTML = '<div style="padding:2rem; text-align:center;"><i class="fa-solid fa-circle-notch fa-spin fa-2x"></i></div>';

    fetch(`/candidate/${candidateId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                content.innerHTML = `<p class="text-red">${data.error}</p>`;
            } else {
                content.innerHTML = data.html;
                // Re-initialize charts if needed
                if (window.initModalCharts) window.initModalCharts();
            }
        })
        .catch(err => {
            console.error(err);
            content.innerHTML = '<p class="text-red">Failed to load candidate data.</p>';
        });
}

function closeModal() {
    const backdrop = document.getElementById('modal-backdrop');
    backdrop.classList.add('hidden');
}

function triggerUpload() {
    document.getElementById('cvsInput').click();
}

function deleteCandidate(id) {
    if (confirm('Are you sure you want to delete this candidate?')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/candidate/${id}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}
// Initialize Charts for Modal
window.initModalCharts = function () {
    const dataDiv = document.getElementById('chart-data');
    if (!dataDiv) return;

    const semantic = parseFloat(dataDiv.dataset.semantic);
    const skills = parseFloat(dataDiv.dataset.skills);
    const experience = parseFloat(dataDiv.dataset.experience);
    const total = parseFloat(dataDiv.dataset.total);

    const ctx = document.getElementById('skillsRadar').getContext('2d');

    // Destroy existing chart if any (to avoid overlapping)
    if (window.modalRadarChart) {
        window.modalRadarChart.destroy();
    }

    window.modalRadarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Semantic', 'Skills', 'Experience', 'Relevance', 'Impact'],
            datasets: [{
                label: 'Candidate Score',
                data: [
                    semantic,
                    skills,
                    experience,
                    total,
                    (total * 0.95).toFixed(1) // Synthesized metric for visual balance
                ],
                backgroundColor: 'rgba(99, 102, 241, 0.25)',
                borderColor: '#6366f1',
                pointBackgroundColor: '#fff',
                pointBorderColor: '#6366f1',
                pointHoverBackgroundColor: '#6366f1',
                pointHoverBorderColor: '#fff',
                borderWidth: 3,
                pointRadius: 4
            },
            {
                label: 'Ideal Profile',
                data: [100, 100, 100, 100, 100],
                fill: true,
                backgroundColor: 'transparent',
                borderColor: 'rgba(255, 255, 255, 0.05)',
                borderDash: [5, 5],
                pointRadius: 0,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim(),
                        font: { size: 12, family: "'Outfit', sans-serif" }
                    },
                    ticks: { display: false, backdropColor: 'transparent' },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#cbd5e1',
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false
                }
            }
        }
    });
};
