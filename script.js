document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
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
    const clearOriginalBtn = document.getElementById('clearOriginalBtn');
    const clearModifiedBtn = document.getElementById('clearModifiedBtn');
    const loadingAnimation = document.querySelector('.loading-animation');
    const apiStatusEl = document.querySelector('.api-status');
    
    // State
    let currentMode = 'fluency';
    let apiStatus = false;
    const maxCharLimit = 1500;
    
    // Initialize the application
    init();
    
    function init() {
      checkApiStatus();
      updateCharacterCount();
      initializeButtonVisibility();
      loadSavedMode();
      attachEventListeners();
    }
    
    function initializeButtonVisibility() {
      // Set initial visibility based on content
      const hasOriginalContent = originalText.value.trim().length > 0;
      const hasModifiedContent = paraphrasedText.value.trim().length > 0;
      
      clearOriginalBtn.style.display = hasOriginalContent ? 'flex' : 'none';
      clearModifiedBtn.style.display = hasModifiedContent ? 'flex' : 'none';
      
      if (hasModifiedContent) {
        textAreaContainer.classList.add('has-content');
        placeholderContent.style.display = 'none';
        paraphrasedText.style.display = 'block';
        addCopyButton();
      } else {
        textAreaContainer.classList.remove('has-content');
        placeholderContent.style.display = 'flex';
        paraphrasedText.style.display = 'none';
      }
    }
    
    function loadSavedMode() {
      // Try to load saved mode from localStorage
      const savedMode = localStorage.getItem('paraphraser-mode');
      if (savedMode) {
        currentMode = savedMode;
        const modeName = document.querySelector(`.mode-option[data-mode="${savedMode}"] h4`)?.textContent || 'Fluency';
        modeValue.textContent = modeName;
      }
    }
    
    function attachEventListeners() {
      // Text input event
      originalText.addEventListener('input', updateCharacterCount);
      
      // Clear buttons
      clearOriginalBtn.addEventListener('click', clearOriginalText);
      clearModifiedBtn.addEventListener('click', clearModifiedText);
      
      // Sample text button
      sampleTextBtn.addEventListener('click', insertSampleText);
      
      // Mode selector
      modeSelector.addEventListener('click', openModeModal);
      modeOptions.forEach(option => {
        option.addEventListener('click', selectMode);
      });
      
      // Modal close button
      closeModal.addEventListener('click', () => modal.style.display = 'none');
      
      // Close modal when clicking outside
      window.addEventListener('click', (event) => {
        if (event.target === modal) modal.style.display = 'none';
      });
      
      // Paraphrase button
      paraphraseBtn.addEventListener('click', paraphraseText);
      
      // Add to Chrome button
      document.getElementById('addToChrome').addEventListener('click', () => {
        alert('This is a demo application. Chrome extension functionality is not available.');
      });
      
      // Add keyboard shortcut (Ctrl+Enter) to trigger paraphrasing
      originalText.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
          if (!paraphraseBtn.disabled) {
            paraphraseText();
          }
        }
      });
    }
    
    function checkApiStatus() {
      fetch('/api-status')
        .then(response => {
          if (!response.ok) throw new Error('API status check failed');
          return response.json();
        })
        .then(data => {
          apiStatus = data.api_configured;
          updateApiStatusDisplay(apiStatus);
        })
        .catch(error => {
          console.error('Could not check API status:', error);
          updateApiStatusDisplay(false);
        });
    }
    
    function updateApiStatusDisplay(isOnline) {
      apiStatusEl.classList.toggle('online', isOnline);
      apiStatusEl.classList.toggle('offline', !isOnline);
      apiStatusEl.innerHTML = `<i class="fa-solid fa-circle"></i><span>API: ${isOnline ? 'Connected' : 'Local Mode'}</span>`;
    }
    
    function updateCharacterCount() {
      const count = originalText.value.length;
      originalCounter.textContent = count;
      
      // Update clear button visibility
      clearOriginalBtn.style.display = count > 0 ? 'flex' : 'none';
      
      // Update paraphrase button state
      const isOverLimit = count > maxCharLimit;
      const isEmpty = count === 0;
      paraphraseBtn.disabled = isOverLimit || isEmpty;
      paraphraseBtn.classList.toggle('disabled', isOverLimit || isEmpty);
      
      // Show warning if over character limit
      if (isOverLimit) {
        originalCounter.style.color = '#f44336';
      } else {
        originalCounter.style.color = '';
      }
    }
    
    function clearOriginalText(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      
      originalText.value = '';
      updateCharacterCount();
      console.log('Original text cleared');
    }
    
    function clearModifiedText(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      
      textAreaContainer.classList.remove('has-content');
      paraphrasedText.value = '';
      paraphrasedText.style.display = 'none';
      placeholderContent.style.display = 'flex';
      paraphrasedCounter.textContent = '0';
      clearModifiedBtn.style.display = 'none';
      
      // Remove copy button
      const copyBtn = document.querySelector('.copy-btn');
      if (copyBtn) copyBtn.remove();
      
      console.log('Modified text cleared');
    }
    
    function insertSampleText() {
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
      updateCharacterCount();
      originalText.focus();
    }
    
    function openModeModal() {
      modal.style.display = 'block';
      
      // Highlight current mode
      modeOptions.forEach(option => {
        option.classList.toggle('active', option.dataset.mode === currentMode);
      });
    }
    
    function selectMode() {
      currentMode = this.dataset.mode;
      modeValue.textContent = this.querySelector('h4').textContent;
      
      // Save selected mode to localStorage
      localStorage.setItem('paraphraser-mode', currentMode);
      
      // Update active class
      modeOptions.forEach(opt => opt.classList.remove('active'));
      this.classList.add('active');
      
      // Close modal
      modal.style.display = 'none';
    }
    
    function paraphraseText() {
      const text = originalText.value.trim();
      if (text === '' || paraphraseBtn.disabled) return;
      
      // Show loading state
      textAreaContainer.classList.add('has-content');
      placeholderContent.style.display = 'none';
      paraphrasedText.style.display = 'block';
      paraphrasedText.value = 'Paraphrasing...';
      loadingAnimation.style.display = 'block';
      clearModifiedBtn.style.display = 'none'; // Hide until processing complete
      
      // Disable the button while processing
      paraphraseBtn.disabled = true;
      paraphraseBtn.classList.add('processing');
      
      // Set timeout for API requests
      const timeoutDuration = 20000; // 20 seconds
      let timeoutId = setTimeout(() => {
        console.warn("API request timed out, attempting local fallback");
        // Make a new request with force_local flag
        makeParaphraseRequest(text, currentMode, true)
          .then(handleParaphraseResult)
          .catch(handleParaphraseError);
      }, timeoutDuration);
      
      // Make API call
      makeParaphraseRequest(text, currentMode, !apiStatus)
        .then(result => {
          clearTimeout(timeoutId); // Clear timeout on success
          handleParaphraseResult(result);
        })
        .catch(error => {
          clearTimeout(timeoutId); // Clear timeout on error
          handleParaphraseError(error);
        });
    }
    
    function handleParaphraseResult(result) {
      // Hide loading animation
      loadingAnimation.style.display = 'none';
      
      // Update UI with the paraphrased text
      textAreaContainer.classList.add('has-content');
      paraphrasedText.value = result;
      paraphrasedCounter.textContent = result.length;
      clearModifiedBtn.style.display = 'flex';
      
      // Add a copy button
      addCopyButton();
      
      // Re-enable the button after processing is complete
      setTimeout(() => {
        paraphraseBtn.disabled = false;
        paraphraseBtn.classList.remove('processing');
      }, 500);
    }
    
    function handleParaphraseError(error) {
      console.error('Paraphrasing error:', error);
      loadingAnimation.style.display = 'none';
      
      textAreaContainer.classList.add('has-content');
      paraphrasedText.value = "Sorry, we couldn't paraphrase your text. Please try again with a shorter or simpler text.";
      clearModifiedBtn.style.display = 'flex';
      
      // Re-enable the button after processing is complete
      setTimeout(() => {
        paraphraseBtn.disabled = false;
        paraphraseBtn.classList.remove('processing');
      }, 500);
    }
    
    async function makeParaphraseRequest(text, mode, forceLocal = false) {
      // Add a retry mechanism
      const maxRetries = 2;
      let retryCount = 0;
      
      while (retryCount <= maxRetries) {
        try {
          const response = await fetch('/paraphrase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, mode, force_local: forceLocal })
          });
          
          // Check for HTTP errors
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: `HTTP error ${response.status}` }));
            throw new Error(errorData.error || `Server error: ${response.status}`);
          }
          
          // Parse response
          const data = await response.json();
          
          // Check for API error in response
          if (data.error) {
            throw new Error(data.error);
          }
          
          // Success - return result
          return data.result;
        } catch (error) {
          retryCount++;
          console.warn(`Request attempt ${retryCount}/${maxRetries + 1} failed:`, error.message);
          
          // For network errors or if already using local mode, don't retry
          if (forceLocal || retryCount > maxRetries || error.message.includes('NetworkError')) {
            throw error;
          }
          
          // Last retry attempt - use force_local
          if (retryCount === maxRetries) {
            console.log("Final retry with local fallback");
            forceLocal = true;
          }
          
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }
    
    function addCopyButton() {
      // Remove existing copy button if present
      const existingCopyBtn = document.querySelector('.copy-btn');
      if (existingCopyBtn) existingCopyBtn.remove();
      
      // Create and add new copy button
      const copyBtn = document.createElement('button');
      copyBtn.className = 'text-control-btn copy-btn';
      copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i><span>Copy</span>';
      
      copyBtn.addEventListener('click', function() {
        copyText(paraphrasedText.value, this);
      });
      
      textAreaContainer.appendChild(copyBtn);
    }
    
    function copyText(text, button) {
      // Try to use the modern Clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text)
          .then(() => updateCopyButton(button, true))
          .catch(() => {
            // Fall back to the execCommand method
            fallbackCopyText(text, button);
          });
      } else {
        // Use the fallback for non-secure contexts
        fallbackCopyText(text, button);
      }
    }
    
    function fallbackCopyText(text, button) {
      // Select the text
      paraphrasedText.select();
      paraphrasedText.setSelectionRange(0, 99999); // For mobile devices
      
      // Try to copy
      let successful = false;
      try {
        successful = document.execCommand('copy');
      } catch (err) {
        console.error('Unable to copy text: ', err);
      }
      
      // Update button state based on success
      updateCopyButton(button, successful);
      
      // Deselect the text to avoid confusion
      window.getSelection().removeAllRanges();
    }
    
    function updateCopyButton(button, success) {
      if (success) {
        button.innerHTML = '<i class="fa-solid fa-check"></i><span>Copied</span>';
        button.classList.add('copied');
        
        // Reset after 2 seconds
        setTimeout(() => {
          button.innerHTML = '<i class="fa-regular fa-copy"></i><span>Copy</span>';
          button.classList.remove('copied');
        }, 2000);
      } else {
        button.innerHTML = '<i class="fa-solid fa-xmark"></i><span>Failed</span>';
        
        // Reset after 2 seconds
        setTimeout(() => {
          button.innerHTML = '<i class="fa-regular fa-copy"></i><span>Copy</span>';
        }, 2000);
      }
    }
});

