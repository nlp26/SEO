/**
 * SEO Analyzer Pro - Frontend Script
 * Handles UI interactions and API communication
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const urlInput = document.getElementById('urlInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    // Initialize tabs functionality
    initTabs();
    
    // Add event listeners
    analyzeBtn.addEventListener('click', analyzeUrl);
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeUrl();
        }
    });

    /**
     * Initializes tab switching functionality
     */
    function initTabs() {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.getAttribute('data-tab');
                switchTab(tabId);
            });
        });
    }

    /**
     * Switches between tabs
     * @param {string} tabId - ID of the tab to activate
     */
    function switchTab(tabId) {
        // Remove active class from all tabs and contents
        tabs.forEach(tab => tab.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Add active class to selected tab and content
        document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
        document.getElementById(`${tabId}-content`).classList.add('active');
    }

    /**
     * Main function to analyze URL
     */
    function analyzeUrl() {
        const url = urlInput.value.trim();
        
        if (!url) {
            alert('Please enter a valid URL');
            return;
        }

        // Show loading, hide results
        loading.style.display = 'block';
        results.style.display = 'none';
        
        // Clear previous results
        clearResults();

        // Make API request
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok (${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            console.log('API Response:', data); // Log the response for debugging
            
            // Check for errors in the response
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display results
            displayResults(data);
            
            // Hide loading, show results
            loading.style.display = 'none';
            results.style.display = 'block';
            
            // Switch to performance tab
            switchTab('performance');
        })
        .catch(error => {
            console.error('Error:', error);
            loading.style.display = 'none';
            alert(`Error analyzing URL: ${error.message}. Please try again.`);
        });
    }

    /**
     * Clears all result containers
     */
    function clearResults() {
        document.getElementById('lighthouse-scores').innerHTML = '';
        document.querySelector('#core-vitals tbody').innerHTML = '';
        document.getElementById('optimization-opportunities').innerHTML = '';
        document.getElementById('meta-info').innerHTML = '';
        document.getElementById('heading-structure').innerHTML = '';
        document.getElementById('link-analysis').innerHTML = '';
        document.getElementById('keyword-metrics').innerHTML = '';
        document.getElementById('ai-recommendations').innerHTML = '';
    }

    /**
     * Displays analysis results in the UI
     * @param {Object} data - Analysis results from API
     */
    function displayResults(data) {
        console.log('Displaying Results:', data); // Log the data being displayed
        // Display data for each tab
        displayPerformanceData(data.performance);
        displayTechnicalData(data.technical_audit);
        displayContentData(data.content_analysis);
        displayAiInsightsData(data.ai_insights);
    }

    /**
     * Displays performance data in the Performance tab
     * @param {Object} data - Performance analysis data
     */
    function displayPerformanceData(data) {
        // Display Lighthouse Scores
        const lighthouseContainer = document.getElementById('lighthouse-scores');
        const scores = data.lighthouse_scores;
        
        const scoreIcons = {
            'performance': 'fa-tachometer-alt',
            'accessibility': 'fa-universal-access',
            'best_practices': 'fa-check-circle',
            'seo': 'fa-search'
        };
        
        for (const [key, value] of Object.entries(scores)) {
            const scoreCard = document.createElement('div');
            scoreCard.classList.add('score-card');
            
            const formattedKey = key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            const icon = scoreIcons[key] || 'fa-chart-bar';
            
            scoreCard.innerHTML = `
                <div class="score-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="score-details">
                    <div class="score-value">${value}%</div>
                    <div class="score-label">${formattedKey}</div>
                </div>
            `;
            
            lighthouseContainer.appendChild(scoreCard);
        }
        
        // Display Core Web Vitals
        const vitalsTable = document.querySelector('#core-vitals tbody');
        const vitals = data.core_vitals;
        
        let counter = 1;
        for (const [key, value] of Object.entries(vitals)) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${counter}</td>
                <td>${key}</td>
                <td>${value}</td>
            `;
            vitalsTable.appendChild(row);
            counter++;
        }
        
        // Display Optimization Opportunities
        const opportunitiesContainer = document.getElementById('optimization-opportunities');
        const opportunities = data.opportunities;
        
        for (const [key, value] of Object.entries(opportunities)) {
            const opportunityItem = document.createElement('div');
            opportunityItem.classList.add('opportunity-item');
            
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const valueString = typeof value === 'number' ? `${value.toLocaleString()} <span class="bytes">bytes</span>` : value;
            
            opportunityItem.innerHTML = `
                <div class="opportunity-label">${formattedKey}</div>
                <div class="opportunity-value">${valueString}</div>
                <div class="potential-label">Potential Savings</div>
            `;
            
            opportunitiesContainer.appendChild(opportunityItem);
        }
    }

    /**
     * Displays technical audit data in the Technical Audit tab
     * @param {Object} data - Technical audit data
     */
    function displayTechnicalData(data) {
        // Display Meta Information
        const metaContainer = document.getElementById('meta-info');
        const metaInfo = data.meta || {};
        
        for (const [key, value] of Object.entries(metaInfo)) {
            const metaItem = document.createElement('div');
            metaItem.classList.add('meta-item');
            
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const present = value && value !== 'missing';
            
            metaItem.innerHTML = `
                <div class="meta-item-label">${formattedKey}</div>
                <div class="${present ? 'status-present' : 'status-missing'}">
                    ${present ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-times-circle"></i>'}
                    ${present ? value : 'Missing'}
                </div>
            `;
            
            metaContainer.appendChild(metaItem);
        }
        
        // Display Heading Structure
        const headingContainer = document.getElementById('heading-structure');
        const headings = data.headings || {};
        
        // Create Y-axis labels
        const yAxisLabels = document.createElement('div');
        yAxisLabels.classList.add('y-axis-labels');
        
        // Find max count
        let maxCount = 1;
        for (const key in headings) {
            if (headings[key] > maxCount) {
                maxCount = headings[key];
            }
        }
        
        for (let i = 4; i >= 0; i--) {
            const label = document.createElement('div');
            label.classList.add('y-label');
            label.textContent = Math.round(maxCount * i / 4);
            yAxisLabels.appendChild(label);
        }
        
        headingContainer.appendChild(yAxisLabels);
        
        // Create bars for each heading type
        for (let i = 1; i <= 6; i++) {
            const tag = `H${i}`;
            const count = headings[tag] || 0;
            const heightPercent = (count / maxCount) * 100;
            
            const bar = document.createElement('div');
            bar.classList.add('chart-bar');
            bar.style.height = `${heightPercent}%`;
            
            const label = document.createElement('div');
            label.classList.add('chart-label');
            label.textContent = tag;
            
            bar.appendChild(label);
            headingContainer.appendChild(bar);
        }
        
        // Display Link Analysis
        const linkContainer = document.getElementById('link-analysis');
        const linkData = data.links || {};
        
        // Create stat box for total links
        const totalLinks = linkData.total || 0;
        const statBox = document.createElement('div');
        statBox.classList.add('stat-box');
        statBox.innerHTML = `
            <div class="stat-value">${totalLinks}</div>
            <div class="stat-label">Total Links</div>
        `;
        
        linkContainer.appendChild(statBox);
    }

    /**
     * Displays content analysis data in the Content Analysis tab
     * @param {Object} data - Content analysis data
     */
    function displayContentData(data) {
        const keywordContainer = document.getElementById('keyword-metrics');
        const keywords = data.keywords || [];
        
        if (!keywords || keywords.length === 0) {
            keywordContainer.innerHTML = '<p>No significant keywords found.</p>';
            return;
        }
        
        const keywordTable = document.createElement('table');
        keywordTable.classList.add('vitals-table');
        
        // Create table header
        const tableHead = document.createElement('thead');
        tableHead.innerHTML = `
            <tr>
                <th>Keyword</th>
                <th>Frequency</th>
                <th>Density</th>
            </tr>
        `;
        keywordTable.appendChild(tableHead);
        
        // Create table body
        const tableBody = document.createElement('tbody');
        
        keywords.forEach(keyword => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${keyword.word || '-'}</td>
                <td>${keyword.count || 0}</td>
                <td>${keyword.density || '0.00'}%</td>
            `;
            tableBody.appendChild(row);
        });
        
        keywordTable.appendChild(tableBody);
        keywordContainer.appendChild(keywordTable);
    }

    /**
     * Displays AI insights data in the AI Insights tab
     * @param {Object} data - AI insights data
     */
    function displayAiInsightsData(data) {
        const aiContainer = document.getElementById('ai-recommendations');
        
        // Verifica se data e recommendations existem
        if (!data || !data.recommendations) {
            aiContainer.innerHTML = '<p>No AI recommendations available.</p>';
            return;
        }
        
        const recommendations = data.recommendations;
        
        if (!recommendations || recommendations.length === 0) {
            aiContainer.innerHTML = '<p>No AI recommendations available.</p>';
            return;
        }
        
        // Display recommendations as formatted text
        const recoText = document.createElement('div');
        recoText.innerHTML = recommendations.replace(/\n/g, '<br>');
        
        aiContainer.appendChild(recoText);
    }
});
