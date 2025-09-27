async function analyzeWebsite() {
    const url = document.getElementById('urlInput').value;
    if (!url) return;

    showLoading(true);
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url })
        });

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        displayResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    // Performance Scores
    displayScoreCard('performance', data.performance.performance);
    displayScoreCard('seo', data.performance.seo);
    
    // Core Web Vitals
    const vitalsTable = document.getElementById('core-vitals');
    vitalsTable.innerHTML = Object.entries(data.core_vitals)
        .map(([metric, value]) => `
            <tr>
                <td>${metric}</td>
                <td>${value}</td>
                <td>${getStatusBadge(value)}</td>
            </tr>
        `).join('');

    // Optimization Opportunities
    const opportunitiesList = document.getElementById('opportunities');
    opportunitiesList.innerHTML = Object.entries(data.opportunities)
        .map(([opportunity, savings]) => `
            <li class="opportunity-item">
                <span class="opportunity-name">${opportunity}</span>
                <span class="savings">Potential savings: ${savings}</span>
            </li>
        `).join('');

    // AI Recommendations
    document.getElementById('ai-recommendations').innerHTML = 
        data.recommendations.replace(/\n/g, '<br>');

    document.querySelector('.results-container').classList.remove('hidden');
}

function displayScoreCard(metric, value) {
    const card = document.getElementById(`${metric}-score`);
    card.querySelector('.score-value').textContent = `${value}%`;
    card.querySelector('.progress-bar').style.width = `${value}%`;
}

function showLoading(isLoading) {
    // Implement loading indicator logic here
}

function showError(message) {
    // Implement error display logic here
}

function getStatusBadge(value) {
    // Implement status badge logic here
    return value; // Placeholder
}