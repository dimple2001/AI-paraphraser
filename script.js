document.addEventListener('DOMContentLoaded', function() {
  const originalText = document.getElementById('originalText');
  const paraphrasedText = document.getElementById('paraphrasedText');
  const originalCounter = document.getElementById('originalCounter');
  const paraphrasedCounter = document.getElementById('paraphrasedCounter');
  const paraphraseBtn = document.getElementById('paraphraseBtn');
  const modeSelector = document.querySelector('.mode-selector');
  const modeValue = document.querySelector('.mode-value');
  const modal = document.getElementById('modeModal');
  const closeModal = document.querySelector('.close');
  const modeOptions = document.querySelectorAll('.mode-option');
  const textAreaContainer = document.querySelector('.text-area-container.result');
  const sampleTextBtn = document.querySelector('.sample-text');
  const placeholderContent = document.getElementById('placeholder-content');
  
  let currentMode = 'fluency';
  let apiStatus = false;
  
  // Check API status on load
  fetch('/api-status')
      .then(response => response.json())
      .then(data => {
          apiStatus = data.api_configured;
          if (!apiStatus) {
              console.log('API token not configured, using local fallback');
              // Optionally show a small notification that local paraphrasing is being used
          }
      })
      .catch(error => {
          console.error('Could not check API status:', error);
      });
  
  // Character counter for original text
  originalText.addEventListener('input', function() {
      const count = this.value.length;
      originalCounter.textContent = count;
      
      // Disable the paraphrase button if over character limit or empty
      if (count > 1500 || count === 0) {
          paraphraseBtn.disabled = true;
          paraphraseBtn.classList.add('disabled');
      } else {
          paraphraseBtn.disabled = false;
          paraphraseBtn.classList.remove('disabled');
      }
  });
  
  // Sample text button click handler
  sampleTextBtn.addEventListener('click', function() {
      // Add sample text based on the current mode
      let sampleText = '';
      
      switch(currentMode) {
          case 'fluency':
              sampleText = "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.";
              break;
          case 'academic':
              sampleText = "The empirical evidence suggests that there is a strong correlation between socioeconomic status and educational outcomes. Further research is necessary to understand the causal mechanisms underlying this relationship.";
              break;
          case 'simple':
              sampleText = "Climate change is making the Earth warmer. This happens because we burn too much oil and gas. We need to use more renewable energy to solve this problem.";
              break;
          case 'creative':
              sampleText = "The sunset painted the sky with hues of orange and pink, as the day bid farewell to make way for the night. Stars began to appear, like diamonds scattered across a velvet canvas.";
              break;
          default:
              sampleText = "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.";
      }
      
      originalText.value = sampleText;
      originalCounter.textContent = sampleText.length;
      
      // Enable paraphrase button
      paraphraseBtn.disabled = false;
      paraphraseBtn.classList.remove('disabled');
  });
  
  // Mode selector click handler
  modeSelector.addEventListener('click', function() {
      modal.style.display = 'block';
      
      // Highlight current mode
      modeOptions.forEach(option => {
          if (option.dataset.mode === currentMode) {
              option.classList.add('active');
          } else {
              option.classList.remove('active');
          }
      });
  });
  
  // Mode option click handler
  modeOptions.forEach(option => {
      option.addEventListener('click', function() {
          currentMode = this.dataset.mode;
          modeValue.textContent = this.querySelector('h4').textContent;
          
          // Update active class
          modeOptions.forEach(opt => opt.classList.remove('active'));
          this.classList.add('active');
          
          // Close modal
          modal.style.display = 'none';
      });
  });
  
  // Close modal when clicking on X
  closeModal.addEventListener('click', function() {
      modal.style.display = 'none';
  });
  
  // Close modal when clicking outside
  window.addEventListener('click', function(event) {
      if (event.target === modal) {
          modal.style.display = 'none';
      }
  });
  
  // Paraphrase button click handler
  paraphraseBtn.addEventListener('click', function() {
      if (originalText.value.trim() === '' || paraphraseBtn.disabled) return;
      
      // Show loading state
      textAreaContainer.classList.add('has-content');
      placeholderContent.style.display = 'none';
      paraphrasedText.style.display = 'block';
      paraphrasedText.value = 'Paraphrasing...';
      
      // Disable the button while processing to prevent multiple clicks
      paraphraseBtn.disabled = true;
      paraphraseBtn.classList.add('processing');
      
      // Make API call to the backend
      fetch('/paraphrase', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({
              text: originalText.value,
              mode: currentMode,
              force_local: !apiStatus // Force local if API is not configured
          })
      })
      .then(response => {
          if (!response.ok) {
              return response.json().then(data => {
                  throw new Error(data.error || 'Server error');
              });
          }
          return response.json();
      })
      .then(data => {
          if (data.error) {
              throw new Error(data.error);
          }
          
          // Update UI with the paraphrased text
          textAreaContainer.classList.add('has-content');
          paraphrasedText.value = data.result;
          paraphrasedCounter.textContent = data.result.length;
          
          // Add a copy button when text is available
          addCopyButton();
      })
      .catch(error => {
          console.error('Error:', error);
          
          // Try with local fallback
          if (!error.message.includes("force_local")) {
              console.log("Trying with local fallback");
              fetch('/paraphrase', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                      text: originalText.value,
                      mode: currentMode,
                      force_local: true
                  })
              })
              .then(response => response.json())
              .then(data => {
                  if (data.result) {
                      textAreaContainer.classList.add('has-content');
                      paraphrasedText.value = data.result;
                      paraphrasedCounter.textContent = data.result.length;
                      
                      // Add a copy button when text is available
                      addCopyButton();
                  } else {
                      throw new Error("Local fallback also failed");
                  }
              })
              .catch(e => {
                  textAreaContainer.classList.add('has-content');
                  paraphrasedText.value = "Sorry, we couldn't paraphrase your text. Please try again with a shorter or simpler text.";
              })
              .finally(() => {
                  paraphraseBtn.disabled = false;
                  paraphraseBtn.classList.remove('processing');
              });
          } else {
              textAreaContainer.classList.add('has-content');
              paraphrasedText.value = "Sorry, we couldn't paraphrase your text. Please try again with a shorter or simpler text.";
              paraphraseBtn.disabled = false;
              paraphraseBtn.classList.remove('processing');
          }
      })
      .finally(() => {
          // Re-enable the button after processing is complete
          setTimeout(() => {
              paraphraseBtn.disabled = false;
              paraphraseBtn.classList.remove('processing');
          }, 500);
      });
  });
  
  // Function to add a copy button to the paraphrased text
  function addCopyButton() {
      // Check if copy button already exists
      if (document.querySelector('.copy-btn')) return;
      
      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-btn';
      copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i><span>Copy</span>';
      
      copyBtn.addEventListener('click', function() {
          paraphrasedText.select();
          document.execCommand('copy');
          
          // Show copied message
          this.innerHTML = '<i class="fa-solid fa-check"></i><span>Copied</span>';
          this.classList.add('copied');
          
          // Reset after 2 seconds
          setTimeout(() => {
              this.innerHTML = '<i class="fa-regular fa-copy"></i><span>Copy</span>';
              this.classList.remove('copied');
          }, 2000);
      });
      
      textAreaContainer.appendChild(copyBtn);
  }
  
  // Add to Chrome button click handler
  document.getElementById('addToChrome').addEventListener('click', function() {
      alert('This is a demo application. Chrome extension functionality is not available.');
  });
  
  // Add CSS for any missing styles directly in JS
  const style = document.createElement('style');
  style.textContent = `
    .text-area-container {
      position: relative;
      width: 100%;
    }
    
    textarea#originalText {
      width: 100%;
      min-height: 200px;
      padding: 15px;
      padding-bottom: 45px; /* Make room for the button */
      resize: vertical;
    }
    
    .sample-text {
      position: absolute;
      bottom: 10px;
      right: 10px;
      background: rgba(245, 245, 245, 0.9);
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 5px 10px;
      cursor: pointer;
      font-size: 0.9rem;
      z-index: 10;
    }
    
    .app-header {
      width: 100%;
      text-align: center;
      margin-bottom: 20px;
      display: block;
    }
    
    .app-header h1 {
      font-size: 2.2rem;
      margin-bottom: 0.5rem;
      color: #333;
    }
    
    .app-description {
      font-size: 1rem;
      color: #666;
    }
    
    .copy-btn {
      position: absolute;
      bottom: 10px;
      right: 10px;
      background: rgba(245, 245, 245, 0.9);
      border: 1px solid #ccc;
      border-radius: 4px;
      padding: 5px 10px;
      cursor: pointer;
      font-size: 0.9rem;
      z-index: 10;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    
    .copy-btn.copied {
      background: #e8f5e9;
      border-color: #66bb6a;
      color: #2e7d32;
    }
    
    .paraphrase-btn.disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .paraphrase-btn.processing {
      opacity: 0.7;
      cursor: wait;
      background-color: #e0e0e0;
    }
  `;
  document.head.appendChild(style);
});