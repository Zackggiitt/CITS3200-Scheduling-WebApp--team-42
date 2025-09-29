document.addEventListener('DOMContentLoaded', () => {
  console.log('Admin dashboard loaded');
  
  const notifBtn = document.getElementById('adminNotifBtn');
  if (!notifBtn) return;

  notifBtn.addEventListener('click', () => {
    const badge = notifBtn.querySelector('.notif-badge');
    if (badge) {
      // Example behavior: mark notifications as read (hide badge)
      badge.remove();
    }
  });

  // Tab switching functionality
  const tabs = document.querySelectorAll('.admin-tab');
  const facilitatorManagement = document.querySelector('.facilitator-management');
  const unitStatusCard = document.querySelector('.unit-status-card');
  const welcomeBanner = document.querySelector('.admin-welcome-banner');

  // Initialize dashboard state on page load
  function initializeDashboard() {
    console.log('Initializing dashboard state...');
    
    // Check if there's a tab parameter in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab');
    
    if (activeTab === 'employees') {
      // Activate employees tab
      const employeesTab = document.querySelector('.admin-tab[data-tab="employees"]');
      if (employeesTab) {
        employeesTab.classList.add('active');
        // Remove active from dashboard tab
        const dashboardTab = document.querySelector('.admin-tab[data-tab="dashboard"]');
        if (dashboardTab) dashboardTab.classList.remove('active');
      }
      
      // Show facilitator management and hide dashboard content
      if (welcomeBanner) welcomeBanner.style.display = 'none';
      if (unitStatusCard) unitStatusCard.style.display = 'none';
      if (facilitatorManagement) facilitatorManagement.style.display = 'block';
      
      console.log('Employees tab activated from URL parameter');
    } else {
      // Default to dashboard tab
    const dashboardTab = document.querySelector('.admin-tab[data-tab="dashboard"]');
    if (dashboardTab) {
      dashboardTab.classList.add('active');
    }
    
    // Show dashboard content and hide facilitator management
    if (welcomeBanner) welcomeBanner.style.display = 'block';
    if (unitStatusCard) unitStatusCard.style.display = 'block';
    if (facilitatorManagement) facilitatorManagement.style.display = 'none';
    
    console.log('Dashboard initialized - facilitator management hidden');
    }
  }

  // Initialize on page load
  initializeDashboard();

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active class from all tabs
      tabs.forEach(t => t.classList.remove('active'));
      // Add active class to clicked tab
      tab.classList.add('active');
      
      // Get the tab data attribute
      const tabName = tab.getAttribute('data-tab');
      console.log(`Switched to ${tabName} tab`);
      
      // Show/hide content sections based on tab
      if (tabName === 'dashboard') {
        // Show dashboard content
        if (welcomeBanner) welcomeBanner.style.display = 'block';
        if (unitStatusCard) unitStatusCard.style.display = 'block';
        if (facilitatorManagement) facilitatorManagement.style.display = 'none';
      } else if (tabName === 'employees') {
        // Show facilitator management
        if (welcomeBanner) welcomeBanner.style.display = 'none';
        if (unitStatusCard) unitStatusCard.style.display = 'none';
        if (facilitatorManagement) facilitatorManagement.style.display = 'block';
      } else {
        // For other tabs (schedule, session-swaps), show dashboard content for now
        if (welcomeBanner) welcomeBanner.style.display = 'block';
        if (unitStatusCard) unitStatusCard.style.display = 'block';
        if (facilitatorManagement) facilitatorManagement.style.display = 'none';
      }
    });
  });

  // Settings button functionality
  const settingsBtn = document.querySelector('.admin-settings-btn');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      console.log('Settings button clicked');
      // Add settings functionality here
      alert('Settings panel coming soon!');
    });
  }

  // Modal functionality
  const modal = document.getElementById('addEmployeeModal');
  const closeModalBtn = document.getElementById('closeModal');
  const cancelBtn = document.getElementById('cancelBtn');
  const addEmployeeForm = document.getElementById('addEmployeeForm');

  // Show modal when Add Employee button is clicked (using event delegation)
  document.addEventListener('click', (e) => {
    // Check if the clicked element is the Add Employee button
    if (e.target.closest('.facilitator-action-btn.primary')) {
      e.preventDefault();
      console.log('Add Employee button clicked!');
      if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
      }
    }
  });

  // Hide modal when close button is clicked
  if (closeModalBtn && modal) {
    closeModalBtn.addEventListener('click', () => {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto'; // Restore scrolling
    });
  }

  // Hide modal when cancel button is clicked
  if (cancelBtn && modal) {
    cancelBtn.addEventListener('click', () => {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto'; // Restore scrolling
    });
  }

  // Hide modal when clicking outside of it
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
      }
    });
  }

  // Handle form submission
  if (addEmployeeForm) {
    addEmployeeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Get form data
      const formData = new FormData(addEmployeeForm);
      const employeeData = {
        role: formData.get('role'),
        fullName: formData.get('fullName'),
        phone: formData.get('phone'),
        position: formData.get('position'),
        email: formData.get('email'),
        status: formData.get('status')
      };

      console.log('Submitting employee data:', employeeData);
      
      // Show loading state
      const submitBtn = addEmployeeForm.querySelector('.btn-primary');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Adding...';
      submitBtn.disabled = true;
      
      try {
        // Send data to backend
        const response = await fetch('/admin/create-employee', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
          },
          body: JSON.stringify(employeeData)
        });
        
        const result = await response.json();
        
        if (result.success) {
          // Success - show success message and close modal
          alert('Employee added successfully! They will receive login credentials via email.');
          modal.style.display = 'none';
          document.body.style.overflow = 'auto';
          
          // Reset form
          addEmployeeForm.reset();
          
          // Refresh the page to show the new facilitator and stay on employees tab
          window.location.href = '/admin/dashboard?tab=employees';
        } else {
          // Error - show error message
          alert(`Error: ${result.error}`);
        }
      } catch (error) {
        console.error('Error submitting form:', error);
        alert('An error occurred while adding the employee. Please try again.');
      } finally {
        // Restore button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Close modal with Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto'; // Restore scrolling
    }
  });

  // Edit Employee Modal functionality
  const editModal = document.getElementById('editEmployeeModal');
  const closeEditModalBtn = document.getElementById('closeEditModal');
  const cancelEditBtn = document.getElementById('cancelEditBtn');
  const editEmployeeForm = document.getElementById('editEmployeeForm');

  // Hide edit modal when close button is clicked
  if (closeEditModalBtn && editModal) {
    closeEditModalBtn.addEventListener('click', () => {
      editModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  // Hide edit modal when cancel button is clicked
  if (cancelEditBtn && editModal) {
    cancelEditBtn.addEventListener('click', () => {
      editModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  // Hide edit modal when clicking outside of it
  if (editModal) {
    editModal.addEventListener('click', (e) => {
      if (e.target === editModal) {
        editModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  }

  // Handle edit form submission
  if (editEmployeeForm) {
    editEmployeeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Get form data
      const formData = new FormData(editEmployeeForm);
      const employeeData = {
        employeeId: formData.get('employeeId'),
        role: formData.get('role'),
        fullName: formData.get('fullName'),
        phone: formData.get('phone'),
        position: formData.get('position'),
        email: formData.get('email'),
        status: formData.get('status')
      };

      console.log('Updating employee data:', employeeData);
      
      // Show loading state
      const submitBtn = editEmployeeForm.querySelector('.btn-primary');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Updating...';
      submitBtn.disabled = true;
      
      try {
        // Send data to backend
        const response = await fetch('/admin/update-employee', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
          },
          body: JSON.stringify(employeeData)
        });
        
        const result = await response.json();
        
        if (result.success) {
          // Success - show success message and close modal
          alert('Employee details updated successfully!');
          editModal.style.display = 'none';
          document.body.style.overflow = 'auto';
          
          // Refresh the page to show updated data
          window.location.href = '/admin/dashboard?tab=employees';
        } else {
          // Error - show error message
          alert(`Error: ${result.error}`);
        }
      } catch (error) {
        console.error('Error updating employee:', error);
        alert('An error occurred while updating the employee. Please try again.');
      } finally {
        // Restore button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Close edit modal with Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && editModal && editModal.style.display === 'flex') {
      editModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  });

  // Search and filter functionality
  const searchInput = document.getElementById('facilitatorSearch');
  const positionFilter = document.getElementById('positionFilter');
  const statusFilter = document.getElementById('statusFilter');
  const facilitatorCards = document.querySelectorAll('.facilitator-card');
  const resultsCount = document.getElementById('resultsCount');

  function filterFacilitators() {
    const searchTerm = searchInput.value.toLowerCase();
    const positionValue = positionFilter.value;
    const statusValue = statusFilter.value;
    
    let visibleCount = 0;
    
    facilitatorCards.forEach(card => {
      const name = card.querySelector('.facilitator-name').textContent.toLowerCase();
      const email = card.querySelector('.facilitator-email').textContent.toLowerCase();
      const positionBadge = card.querySelector('.badge-position') ? card.querySelector('.badge-position').textContent.toLowerCase() : '';
      const statusBadge = card.querySelector('.badge-status').textContent.toLowerCase();
      
      // Check search term
      const matchesSearch = searchTerm === '' || 
        name.includes(searchTerm) || 
        email.includes(searchTerm);
      
      // Check filters - map position filter values to badge text
      let matchesPosition = true;
      if (positionValue !== '') {
        if (positionValue === 'admin') {
          matchesPosition = positionBadge.includes('admin');
        } else if (positionValue === 'facilitator') {
          matchesPosition = positionBadge.includes('facilitator');
        } else if (positionValue === 'unit_coordinator') {
          matchesPosition = positionBadge.includes('unit') && positionBadge.includes('coordinator');
        }
      }
      
      const matchesStatus = statusValue === '' || statusBadge.includes(statusValue);
      
      if (matchesSearch && matchesPosition && matchesStatus) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });
    
    // Update results count
    if (resultsCount) {
      resultsCount.textContent = `Showing ${visibleCount} of ${facilitatorCards.length} employees`;
    }
  }

  // Add event listeners for search and filters
  if (searchInput) {
    searchInput.addEventListener('input', filterFacilitators);
  }
  if (positionFilter) {
    positionFilter.addEventListener('change', filterFacilitators);
  }
  if (statusFilter) {
    statusFilter.addEventListener('change', filterFacilitators);
  }

  // Conditional Role dropdown functionality
  const positionSelect = document.getElementById('position');
  const roleGroup = document.getElementById('roleGroup');
  const roleSelect = document.getElementById('role');
  
  function toggleRoleDropdown() {
    const selectedPosition = positionSelect.value;
    
    if (selectedPosition === 'facilitator') {
      roleGroup.style.display = 'block';
      roleSelect.setAttribute('required', 'required');
      // Set default value when showing
      roleSelect.value = 'lab_facilitator';
    } else {
      roleGroup.style.display = 'none';
      roleSelect.removeAttribute('required');
      // Clear value when hiding
      roleSelect.value = '';
    }
  }
  
  // Add event listener for position change
  if (positionSelect) {
    positionSelect.addEventListener('change', toggleRoleDropdown);
  }

  // Edit Modal Conditional Role dropdown functionality
  const editPositionSelect = document.getElementById('editPosition');
  const editRoleGroup = document.getElementById('editRoleGroup');
  const editRoleSelect = document.getElementById('editRole');
  
  function toggleEditRoleDropdown() {
    const selectedPosition = editPositionSelect.value;
    
    if (selectedPosition === 'facilitator') {
      editRoleGroup.style.display = 'block';
      editRoleSelect.setAttribute('required', 'required');
      // Set default value when showing
      editRoleSelect.value = 'lab_facilitator';
    } else {
      editRoleGroup.style.display = 'none';
      editRoleSelect.removeAttribute('required');
      // Clear value when hiding
      editRoleSelect.value = '';
    }
  }
  
  // Add event listener for edit position change
  if (editPositionSelect) {
    editPositionSelect.addEventListener('change', toggleEditRoleDropdown);
  }

  // Close dropdowns when clicking outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown-container')) {
      const dropdowns = document.querySelectorAll('.dropdown-menu');
      dropdowns.forEach(dropdown => {
        dropdown.style.display = 'none';
      });
    }
  });

});

// Dropdown functionality
function toggleDropdown(facilitatorId) {
  const dropdown = document.getElementById(`dropdown-${facilitatorId}`);
  const allDropdowns = document.querySelectorAll('.dropdown-menu');
  
  // Close all other dropdowns
  allDropdowns.forEach(d => {
    if (d.id !== `dropdown-${facilitatorId}`) {
      d.style.display = 'none';
    }
  });
  
  // Toggle current dropdown
  if (dropdown.style.display === 'none' || dropdown.style.display === '') {
    dropdown.style.display = 'block';
  } else {
    dropdown.style.display = 'none';
  }
}

// Disable account function
function disableAccount(facilitatorId, facilitatorName) {
  if (confirm(`Are you sure you want to disable ${facilitatorName}'s account?`)) {
    // TODO: Implement disable account API call
    console.log(`Disabling account for facilitator ID: ${facilitatorId}`);
    alert(`${facilitatorName}'s account has been disabled.`);
    // Close dropdown
    document.getElementById(`dropdown-${facilitatorId}`).style.display = 'none';
  }
}

// Delete account function
async function deleteAccount(facilitatorId, facilitatorName) {
  console.log(`Attempting to delete facilitator ID: ${facilitatorId}, Name: ${facilitatorName}`);
  
  if (confirm(`Are you sure you want to permanently delete ${facilitatorName}'s account? This action cannot be undone.`)) {
    try {
      // Get CSRF token
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      console.log('CSRF Token:', csrfToken);
      
      // Send DELETE request to backend
      console.log(`Sending DELETE request to: /admin/delete-employee/${facilitatorId}`);
      const response = await fetch(`/admin/delete-employee/${facilitatorId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        }
      });
      
      console.log('Response status:', response.status);
      const result = await response.json();
      console.log('Response result:', result);
      
      if (result.success) {
        // Success - remove the facilitator card from DOM
        const facilitatorCard = document.querySelector(`.facilitator-card[data-facilitator-id="${facilitatorId}"]`);
        if (facilitatorCard) {
          facilitatorCard.remove();
        }
        
        // Update results count
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
          const currentText = resultsCount.textContent;
          const match = currentText.match(/Showing (\d+) of (\d+) facilitators/);
          if (match) {
            const currentVisible = parseInt(match[1]) - 1;
            const total = parseInt(match[2]) - 1;
            resultsCount.textContent = `Showing ${currentVisible} of ${total} facilitators`;
          }
        }
        
        alert(`${facilitatorName}'s employee account has been deleted successfully.`);
        
        // Refresh the page to update all counts and ensure consistency
        window.location.href = '/admin/dashboard?tab=employees';
      } else {
        alert(`Error: ${result.message || 'Failed to delete account'}`);
      }
    } catch (error) {
      console.error('Error deleting facilitator:', error);
      alert('An error occurred while deleting the account. Please try again.');
    }
    
    // Close dropdown
    document.getElementById(`dropdown-${facilitatorId}`).style.display = 'none';
  }
}

// Open edit modal function
function openEditModal(facilitatorId, facilitatorName, facilitatorEmail) {
  console.log(`Opening edit modal for employee ID: ${facilitatorId}, Name: ${facilitatorName}`);
  
  // Set the employee ID
  document.getElementById('editEmployeeId').value = facilitatorId;
  
  // Set the email
  document.getElementById('editEmail').value = facilitatorEmail;
  
  // Set the full name
  document.getElementById('editFullName').value = facilitatorName;
  
  // Find the employee card and extract additional data
  const employeeCard = document.querySelector(`.facilitator-card[data-facilitator-id="${facilitatorId}"]`);
  if (employeeCard) {
    // Extract phone number from details
    const phoneElement = employeeCard.querySelector('.facilitator-phone');
    if (phoneElement) {
      document.getElementById('editPhone').value = phoneElement.textContent.trim();
    }
    
    // Extract position from badge
    const positionElement = employeeCard.querySelector('.badge-position');
    if (positionElement) {
      const positionText = positionElement.textContent.trim();
      console.log('Position badge text:', positionText);
      
      // Map position text to dropdown values
      let positionValue = '';
      if (positionText.toLowerCase().includes('facilitator')) {
        positionValue = 'facilitator';
      } else if (positionText.toLowerCase().includes('unit') && positionText.toLowerCase().includes('coordinator')) {
        positionValue = 'unit_coordinator';
      } else if (positionText.toLowerCase().includes('admin')) {
        positionValue = 'admin';
      }
      
      console.log('Setting position value to:', positionValue);
      document.getElementById('editPosition').value = positionValue;
      
      // Trigger role dropdown visibility based on position
      if (positionValue === 'facilitator') {
        // Extract role from badge
        const roleElement = employeeCard.querySelector('.badge-role');
        if (roleElement) {
          const roleText = roleElement.textContent.trim();
          console.log('Role badge text:', roleText);
          
          // Map role text to dropdown values
          let roleValue = '';
          if (roleText.toLowerCase().includes('lab')) {
            roleValue = 'lab_facilitator';
          } else if (roleText.toLowerCase().includes('senior')) {
            roleValue = 'senior_facilitator';
          } else if (roleText.toLowerCase().includes('lead')) {
            roleValue = 'lead_facilitator';
          }
          
          console.log('Setting role value to:', roleValue);
          document.getElementById('editRoleGroup').style.display = 'block';
          document.getElementById('editRole').value = roleValue;
          document.getElementById('editRole').setAttribute('required', 'required');
        }
      } else {
        document.getElementById('editRoleGroup').style.display = 'none';
        document.getElementById('editRole').removeAttribute('required');
      }
    }
    
    // Extract status from badge
    const statusElement = employeeCard.querySelector('.badge-status');
    if (statusElement) {
      const statusText = statusElement.textContent.trim();
      console.log('Status badge text:', statusText);
      
      // Map status text to dropdown values
      let statusValue = '';
      if (statusText.toLowerCase().includes('active')) {
        statusValue = 'active';
      } else if (statusText.toLowerCase().includes('inactive')) {
        statusValue = 'inactive';
      } else if (statusText.toLowerCase().includes('leave')) {
        statusValue = 'on_leave';
      } else {
        statusValue = 'active'; // Default fallback
      }
      
      console.log('Setting status value to:', statusValue);
      document.getElementById('editStatus').value = statusValue;
    } else {
      // Fallback to 'active' if status badge not found
      document.getElementById('editStatus').value = 'active';
      console.log('No status badge found, defaulting to active');
    }
  }
  
  // Show the modal
  const editModal = document.getElementById('editEmployeeModal');
  if (editModal) {
    editModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

// Send reset link function
async function sendResetLink() {
  const employeeId = document.getElementById('editEmployeeId').value;
  const employeeEmail = document.getElementById('editEmail').value;
  
  if (!employeeId || !employeeEmail) {
    alert('Employee information not found. Please try again.');
    return;
  }
  
  if (confirm(`Send password reset link to ${employeeEmail}?`)) {
    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      const response = await fetch('/admin/send-reset-link', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ employeeId: employeeId, email: employeeEmail })
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Password reset link sent to ${employeeEmail} successfully!`);
      } else {
        alert(`Error: ${result.message || 'Failed to send reset link'}`);
      }
    } catch (error) {
      console.error('Error sending reset link:', error);
      alert('An error occurred while sending the reset link. Please try again.');
    }
  }
}

// Admin reset password function
async function adminResetPassword() {
  const employeeId = document.getElementById('editEmployeeId').value;
  const employeeName = document.getElementById('editFullName').value;
  
  if (!employeeId || !employeeName) {
    alert('Employee information not found. Please try again.');
    return;
  }
  
  // Prompt for new password
  const newPassword = prompt(`Enter new password for ${employeeName}:`);
  if (!newPassword) {
    return; // User cancelled
  }
  
  if (newPassword.length < 6) {
    alert('Password must be at least 6 characters long.');
    return;
  }
  
  if (confirm(`Reset password for ${employeeName}? This will immediately change their password.`)) {
    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      const response = await fetch('/admin/admin-reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ employeeId: employeeId, newPassword: newPassword })
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Password reset successfully for ${employeeName}! They can now log in with the new password.`);
      } else {
        alert(`Error: ${result.message || 'Failed to reset password'}`);
      }
    } catch (error) {
      console.error('Error resetting password:', error);
      alert('An error occurred while resetting the password. Please try again.');
    }
  }
}
