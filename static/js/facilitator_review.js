// Facilitator CSV Review functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle facilitator CSV upload
    const setupCsvInput = document.getElementById('setup_csv');
    const uploadBtn = document.getElementById('uploadSetupBtn');
    const fileNameSpan = document.getElementById('file_name');
    const uploadStatusDiv = document.getElementById('upload_status');
    
    if (setupCsvInput) {
        setupCsvInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                fileNameSpan.textContent = e.target.files[0].name;
            } else {
                fileNameSpan.textContent = 'No file selected';
            }
        });
    }
    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            const file = setupCsvInput.files[0];
            if (!file) {
                showStatusMessage(uploadStatusDiv, 'Please select a CSV file first.', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('setup_csv', file);
            formData.append('unit_id', document.getElementById('unit_id').value);
            
            fetch(UPLOAD_SETUP_CSV, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': CSRF_TOKEN
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.ok) {
                    // Show review section
                    showFacilitatorReview(data.facilitators, data.unit_id);
                } else {
                    showStatusMessage(uploadStatusDiv, data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showStatusMessage(uploadStatusDiv, 'An error occurred while uploading the file.', 'error');
            });
        });
    }
});

function showFacilitatorReview(facilitators, unitId) {
    // Create review section
    const reviewSection = document.createElement('div');
    reviewSection.id = 'facilitator-review';
    reviewSection.className = 'setup-card mt-4';
    
    // Header
    reviewSection.innerHTML = `
        <div class="setup-card__header">
            <span class="material-icons">visibility</span>
            <div>
                <h3 class="setup-card__title">Review Facilitators</h3>
                <p class="setup-card__hint">
                    Please review the facilitators that will be added to this unit. 
                    Accounts will be created for new facilitators with a default password.
                </p>
            </div>
        </div>
    `;
    
    // Facilitator list
    const facilitatorList = document.createElement('div');
    facilitatorList.className = 'facilitator-list mt-4';
    
    facilitators.forEach(facilitator => {
        const facilitatorItem = document.createElement('div');
        facilitatorItem.className = 'facilitator-item flex items-center justify-between p-3 border-b';
        facilitatorItem.innerHTML = `
            <div class="facilitator-info">
                <span class="facilitator-email font-medium">${facilitator.email}</span>
                <span class="facilitator-status text-sm ${facilitator.exists ? 'text-green-600' : 'text-orange-600'}">
                    ${facilitator.exists ? 'Existing account' : 'New account (will be created)'}
                </span>
            </div>
            <div class="facilitator-actions">
                <input type="checkbox" id="fac_${facilitator.row}" name="facilitator_emails" value="${facilitator.email}" checked>
                <label for="fac_${facilitator.row}">Add to unit</label>
            </div>
        `;
        facilitatorList.appendChild(facilitatorItem);
    });
    
    // Action buttons
    const actionButtons = document.createElement('div');
    actionButtons.className = 'action-buttons mt-4 flex gap-3';
    actionButtons.innerHTML = `
        <button type="button" id="confirm-facilitators" class="cal-btn primary">Confirm and Add Facilitators</button>
        <button type="button" id="cancel-review" class="cal-btn">Cancel</button>
    `;
    
    reviewSection.appendChild(facilitatorList);
    reviewSection.appendChild(actionButtons);
    
    // Replace the upload section with review section
    const setupWrap = document.getElementById('setup_wrap');
    setupWrap.parentNode.replaceChild(reviewSection, setupWrap);
    
    // Add event listeners for action buttons
    document.getElementById('confirm-facilitators').addEventListener('click', function() {
        confirmFacilitators(unitId);
    });
    
    document.getElementById('cancel-review').addEventListener('click', function() {
        // Reset the form and show the original upload section
        location.reload();
    });
}

function confirmFacilitators(unitId) {
    // Get selected facilitators
    const checkboxes = document.querySelectorAll('input[name="facilitator_emails"]:checked');
    const facilitatorEmails = Array.from(checkboxes).map(cb => cb.value);
    
    // Create form data
    const formData = new FormData();
    formData.append('unit_id', unitId);
    facilitatorEmails.forEach(email => {
        formData.append('facilitator_emails', email);
    });
    
    // Show loading state
    const confirmBtn = document.getElementById('confirm-facilitators');
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = 'Processing...';
    confirmBtn.disabled = true;
    
    // Send to backend
    fetch('/unitcoordinator/confirm-facilitators', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': CSRF_TOKEN
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.ok) {
            // Show success message
            const uploadStatusDiv = document.getElementById('upload_status') || 
                                  document.createElement('div');
            uploadStatusDiv.id = 'upload_status';
            showStatusMessage(uploadStatusDiv, 
                `Successfully added ${data.linked_facilitators} facilitators to the unit. ` +
                `${data.created_users} new accounts were created.`, 
                'success');
            
            // Update hidden input to indicate setup is complete
            document.getElementById('setup_complete').value = 'true';
            
            // Hide the review section
            document.getElementById('facilitator-review').style.display = 'none';
        } else {
            // Show error message
            const uploadStatusDiv = document.getElementById('upload_status') || 
                                  document.createElement('div');
            uploadStatusDiv.id = 'upload_status';
            showStatusMessage(uploadStatusDiv, data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const uploadStatusDiv = document.getElementById('upload_status') || 
                              document.createElement('div');
        uploadStatusDiv.id = 'upload_status';
        showStatusMessage(uploadStatusDiv, 'An error occurred while processing facilitators.', 'error');
    })
    .finally(() => {
        // Restore button state
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
    });
}

function showStatusMessage(element, message, type) {
    element.textContent = message;
    element.className = 'upload-status ' + (type === 'error' ? 'text-red-600' : 'text-green-600');
    element.classList.remove('hidden');
}
