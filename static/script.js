document.addEventListener('DOMContentLoaded', () => {
    // === Toast Notification System ===
    window.showToast = function (type, title, message, duration = 4000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const icons = {
            success: 'fa-circle-check',
            error: 'fa-circle-xmark',
            warning: 'fa-triangle-exclamation',
            info: 'fa-circle-info'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fa-solid ${icons[type] || icons.info} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fa-solid fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };

    // === Global Loader ===
    window.showLoader = function () {
        const loader = document.getElementById('global-loader');
        if (loader) loader.classList.remove('hidden');
    };

    window.hideLoader = function () {
        const loader = document.getElementById('global-loader');
        if (loader) loader.classList.add('hidden');
    };

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

function toggleEditMode() {
    const container = document.getElementById('edit-form-container');
    if (container) {
        container.classList.toggle('active');
    }
}

// Quick Scan Form Handler
const uploadForm = document.getElementById('uploadForm');
if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const loader = document.getElementById('loader');
        const resultsList = document.getElementById('resultsList');
        const statusValues = document.querySelectorAll('.upload-zone p'); // Optional UI feedback

        // UI Reset
        loader.classList.remove('hidden');
        resultsList.innerHTML = '';

        const formData = new FormData(uploadForm);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            loader.classList.add('hidden');

            if (data.error) {
                resultsList.innerHTML = `<div class="glass-card" style="border-left: 4px solid var(--danger); padding: 1rem;"><p class="text-red">Error: ${data.error}</p></div>`;
                return;
            }

            if (!data.results || data.results.length === 0) {
                resultsList.innerHTML = `<div class="empty-state"><p>No results returned. Ensure documents are readable.</p></div>`;
                return;
            }

            // Render Results
            const statusBadge = document.getElementById('result-status');
            if (statusBadge) { statusBadge.innerText = `Analyzed ${data.results.length} Candidates`; statusBadge.className = 'status-pill open'; }

            data.results.forEach((res, index) => {
                const color = res.total_score >= 80 ? 'success' : (res.total_score >= 50 ? 'warning' : 'danger');
                const card = document.createElement('div');
                card.className = 'glass-card animate-in';
                card.style.animationDelay = `${index * 0.1}s`;
                card.style.padding = '1.25rem';
                card.style.marginBottom = '1rem';
                card.style.display = 'flex';
                card.style.justifyContent = 'space-between';
                card.style.alignItems = 'center';
                card.style.borderLeft = `4px solid var(--${color})`;

                const missingChips = res.missing_skills && res.missing_skills.length > 0
                    ? res.missing_skills.slice(0, 3).map(s => `<span class="tag missing" style="font-size: 0.75rem;">${s}</span>`).join('')
                    : '<span class="text-muted" style="font-size: 0.8rem;">All critical skills matched</span>';

                card.innerHTML = `
                    <div style="flex: 1;">
                        <h4 style="margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                            ${res.filename}
                            <span class="status-pill" style="font-size: 0.7rem; background: rgba(255,255,255,0.05);"> EXP: ${res.years_experience} Yrs</span>
                        </h4>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                            ${missingChips}
                            ${res.missing_skills.length > 3 ? `<span class="text-muted" style="font-size: 0.75rem;">+${res.missing_skills.length - 3} more</span>` : ''}
                        </div>
                    </div>
                    
                    <div style="text-align: right; min-width: 100px;">
                        <span style="font-size: 1.5rem; font-weight: 700; color: var(--${color}); display: block;">${Math.round(res.total_score)}%</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Match Score</span>
                    </div>
                `;
                resultsList.appendChild(card);
            });

        } catch (err) {
            console.error(err);
            loader.classList.add('hidden');
            resultsList.innerHTML = `<div class="glass-card"><p class="text-red">System Error: Failed to analyze documents.</p></div>`;
        }
    });
}

