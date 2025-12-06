function triggerUpload() {
    document.getElementById('cvsInput').click();
}

function viewCandidate(id) {
    const modalBackdrop = document.getElementById('modal-backdrop');
    const modalContent = document.getElementById('modal-content');

    // Show spinner if needed, or just fetch
    modalBackdrop.classList.remove('hidden');
    modalContent.innerHTML = '<div style="padding:2rem; text-align:center;">Loading analysis...</div>';

    fetch(`/candidate/${id}`)
        .then(response => response.json())
        .then(data => {
            modalContent.innerHTML = data.html;
            // Execute scripts in the returned HTML (Chart.js needs this)
            const scripts = modalContent.querySelectorAll("script");
            scripts.forEach((script) => {
                const newScript = document.createElement("script");
                newScript.textContent = script.textContent;
                document.body.appendChild(newScript);
            });
        })
        .catch(err => {
            modalContent.innerHTML = `<div style="padding:2rem; color:red;">Error loading candidate: ${err}</div>`;
        });
}

function deleteCandidate(id) {
    if (confirm('Delete this candidate?')) {
        fetch(`/candidate/${id}/delete`, { method: 'POST' })
            .then(() => window.location.reload());
    }
}

function closeModal() {
    document.getElementById('modal-backdrop').classList.add('hidden');
}

// Close on backdrop click
document.getElementById('modal-backdrop').addEventListener('click', function (e) {
    if (e.target === this) {
        closeModal();
    }
});
