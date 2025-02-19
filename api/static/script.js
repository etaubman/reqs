// Listen for the submit button click event
document.getElementById('submit-button').addEventListener('click', async function () {
    // Hide the ideas area when submit is pressed
    document.getElementById('ideas-buttons').style.display = 'none';
    // Hide the ideas actions (including focus input) as well
    document.getElementById('ideas-actions').style.display = 'none';
    document.getElementById('refresh-ideas').innerText = 'Show Ideas';

    const featureDescription = document.getElementById('feature-input').value;
    if (!featureDescription.trim()) {
        document.getElementById('result').innerText = 'Please enter a feature description';
        return;
    }

    // Replace plain text loading indicator with spinner for feature output
    document.getElementById('result').innerHTML = '<div class="spinner"></div>';
    
    try {
        // Get the base URL of the current page
        const baseUrl = window.location.origin;
        console.log('Base URL:', baseUrl);
        
        console.log('Sending request to generate endpoint');
        const response = await fetch(`${baseUrl}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ description: featureDescription })
        });

        console.log('Response status:', response.status);
        const responseText = await response.text();
        console.log('Response text:', responseText);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}, body: ${responseText}`);
        }

        const data = JSON.parse(responseText);
        if (data.result) {
            console.log('Parsing result:', data.result);
            const parsedResult = JSON.parse(data.result);
            renderFeatureData(parsedResult);
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('result').innerText = 'Error: ' + error.message;
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // NEW: If preloaded data exists, render it immediately
    if(window.preloadedFeatureData) {
        renderFeatureData(window.preloadedFeatureData);
    }
    
    // Load ideas from the API and populate the ideas container on page ready
    async function loadIdeas() {
        const ideasContainer = document.getElementById('ideas-buttons');
        // Replace plain text loading indicator with spinner for ideas
        ideasContainer.innerHTML = '<div class="spinner"></div>';
        try {
            const baseUrl = window.location.origin;
            let focusText = '';
            const focusInput = document.getElementById('focus-input');
            if (focusInput && focusInput.value.trim()) {
                focusText = focusInput.value.trim();
            }
            const url = `${baseUrl}/api/generate-ideas${focusText ? ('?focus=' + encodeURIComponent(focusText)) : ''}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to load ideas');
            const data = await response.json();
            const ideas = JSON.parse(data.result);
            ideasContainer.innerHTML = '';
            ideas.forEach(idea => {
                const btn = document.createElement('button');
                btn.className = 'idea-button';
                btn.innerText = idea.short_title;
                btn.addEventListener('click', function() {
                    document.getElementById('feature-input').value = idea.long_description;
                });
                ideasContainer.appendChild(btn);
            });
        } catch (error) {
            ideasContainer.innerHTML = 'Error loading ideas';
            console.error('Failed to load ideas:', error);
        }
    }
    
    // Updated refresh listener to toggle ideas area
    document.getElementById('refresh-ideas').addEventListener('click', function() {
        const ideasButtons = document.getElementById('ideas-buttons');
        const btn = document.getElementById('refresh-ideas');
        if (ideasButtons.style.display === 'none' || ideasButtons.innerHTML === '') {
            ideasButtons.style.display = 'block';
            btn.innerText = 'Refresh Ideas';
            loadIdeas();
        } else {
            loadIdeas();
        }
    });

    // NEW: Replace "Add Focus" button with an expanding input field on click
    document.getElementById('add-focus').addEventListener('click', function() {
        const actionsContainer = document.getElementById('ideas-actions');
        // Create input element
        const focusInput = document.createElement('input');
        focusInput.id = 'focus-input';
        focusInput.type = 'text';
        focusInput.placeholder = 'e.g. Document Management';
        focusInput.style.width = '0px';
        focusInput.style.transition = 'width 0.5s ease';
        focusInput.style.marginRight = '10px';
        focusInput.style.fontSize = '16px';
        focusInput.style.overflow = 'hidden';
        // Replace the Add Focus button with the input
        this.replaceWith(focusInput);
        // Animate input expansion
        setTimeout(() => {
            focusInput.style.width = '400px';
            document.getElementById('refresh-ideas').style.marginLeft = '10px';
        }, 10);
        // NEW: When user hits enter, refresh ideas
        focusInput.addEventListener('keydown', function(e) {
            if(e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('refresh-ideas').click();
            }
        });
    });
    
    // Only load ideas if no preloaded data exists
    if (!window.preloadedFeatureData) {
        loadIdeas();
    }
});

// Declare a global variable to hold the latest generated data
let currentData = null;

// Render the API response data into a clean HTML layout
function renderFeatureData(data) {
    currentData = data; // store data for downloading markdown
    const resultContainer = document.getElementById('result');
    let html = '';
  
    // Render Epic Section
    html += `<div class="epic">`;
    html += `<div class="epic-title">${data.epic_title}</div>`;
    html += `<div class="epic-description"><strong>Description:</strong> ${data.description}</div>`;
    html += `<div class="epic-rationale"><strong>Rationale:</strong> ${data.rationale}</div>`;
    html += `<div class="epic-long-description"><strong>Long Description:</strong> ${data.long_description}</div>`;
    html += `</div>`;
  
    // Render each Story
    if (data.stories && data.stories.length > 0) {
      data.stories.forEach(story => {
        html += `<div class="story">`;
        html += `<h3>${story.story_title}</h3>`;
        html += `<div class="story-section"><strong>Description:</strong> ${story.description}</div>`;
        html += `<div class="story-section"><strong>Agile Story:</strong> ${story.agile_story}</div>`;
        html += `<div class="story-section"><strong>Purpose:</strong> ${story.purpose}</div>`;
        html += `<div class="story-section"><strong>Rationale:</strong> ${story.rationale}</div>`;
  
        // Acceptance Criteria
        if (story.acceptance_criteria && story.acceptance_criteria.length > 0) {
          html += `<div class="story-section"><strong>Acceptance Criteria:</strong><ul>`;
          story.acceptance_criteria.forEach(crit => {
            html += `<li><em>Criteria:</em> ${crit.criteria}`;
            if (crit.test_criteria && crit.test_criteria.length > 0) {
              html += `<ul class="acceptance-criteria">`;
              crit.test_criteria.forEach(test => {
                html += `<li class="test-criteria">${test}</li>`;
              });
              html += `</ul>`;
            }
            html += `</li>`;
          });
          html += `</ul></div>`;
        }
  
        // Technical Considerations
        if (story.technical_considerations && story.technical_considerations.length > 0) {
          html += `<div class="story-section"><strong>Technical Considerations:</strong><ul class="technical-considerations">`;
          story.technical_considerations.forEach(item => {
            html += `<li>${item}</li>`;
          });
          html += `</ul></div>`;
        }
  
        html += `</div>`;
      });
    }
  
    resultContainer.innerHTML = html;
    // Show download markdown button once content is generated
    document.getElementById('download-markdown-container').style.display = 'block';
  }

// Convert currentData to Markdown string
function convertDataToMarkdown(data) {
    let md = '';
    md += `# ${data.epic_title}\n\n`;
    md += `**Description:** ${data.description}\n\n`;
    md += `**Rationale:** ${data.rationale}\n\n`;
    md += `**Long Description:** ${data.long_description}\n\n`;
    if(data.stories && data.stories.length > 0) {
        md += `## Stories\n\n`;
        data.stories.forEach(story => {
            md += `### ${story.story_title}\n\n`;
            md += `**Description:** ${story.description}\n\n`;
            md += `**Agile Story:** ${story.agile_story}\n\n`;
            md += `**Purpose:** ${story.purpose}\n\n`;
            md += `**Rationale:** ${story.rationale}\n\n`;
            if(story.acceptance_criteria && story.acceptance_criteria.length > 0){
                md += `**Acceptance Criteria:**\n`;
                story.acceptance_criteria.forEach(crit=>{
                    md += `- Criteria: ${crit.criteria}\n`;
                    if(crit.test_criteria && crit.test_criteria.length > 0){
                        crit.test_criteria.forEach(test=>{
                            md += `   - ${test}\n`;
                        });
                    }
                });
                md += `\n`;
            }
            if(story.technical_considerations && story.technical_considerations.length > 0){
                md += `**Technical Considerations:**\n`;
                story.technical_considerations.forEach(item=>{
                    md += `- ${item}\n`;
                });
                md += `\n`;
            }
            md += `\n`;
        });
    }
    return md;
}

// Download markdown functionality
document.getElementById('download-markdown').addEventListener('click', function() {
    if (!currentData) {
        alert('No generated content to download.');
        return;
    }
    const markdown = convertDataToMarkdown(currentData);
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'generated-feature.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});
