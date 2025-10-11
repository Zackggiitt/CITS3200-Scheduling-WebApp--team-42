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
  const dashboardMetrics = document.querySelector('.dashboard-metrics');
  const unitStatusCard = document.querySelector('.unit-status-card');
  const welcomeBanner = document.querySelector('.admin-welcome-banner');

  // Initialize dashboard state on page load
  function initializeDashboard() {
    console.log('Initializing dashboard state...');
    
    // Ensure dashboard tab is active by default
    const dashboardTab = document.querySelector('.admin-tab[data-tab="dashboard"]');
    if (dashboardTab) {
      dashboardTab.classList.add('active');
    }
    
    // Show dashboard content and hide facilitator management
    if (welcomeBanner) welcomeBanner.style.display = 'block';
    if (dashboardMetrics) dashboardMetrics.style.display = 'block';
    if (unitStatusCard) unitStatusCard.style.display = 'block';
    if (facilitatorManagement) facilitatorManagement.style.display = 'none';
    
    console.log('Dashboard initialized - facilitator management hidden');
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
        if (dashboardMetrics) dashboardMetrics.style.display = 'block';
        if (unitStatusCard) unitStatusCard.style.display = 'block';
        if (facilitatorManagement) facilitatorManagement.style.display = 'none';
      } else if (tabName === 'employees') {
        // Show facilitator management
        if (welcomeBanner) welcomeBanner.style.display = 'none';
        if (dashboardMetrics) dashboardMetrics.style.display = 'none';
        if (unitStatusCard) unitStatusCard.style.display = 'none';
        if (facilitatorManagement) facilitatorManagement.style.display = 'block';
      } else {
        // For other tabs (schedule, session-swaps), show dashboard content for now
        if (welcomeBanner) welcomeBanner.style.display = 'block';
        if (dashboardMetrics) dashboardMetrics.style.display = 'block';
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
        experienceLevel: formData.get('experienceLevel'),
        email: formData.get('email'),
        hourlyRate: formData.get('hourlyRate'),
        department: formData.get('department'),
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
        const response = await fetch('/admin/create-facilitator-modal', {
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
          alert('Facilitator added successfully! They will receive login credentials via email.');
          modal.style.display = 'none';
          document.body.style.overflow = 'auto';
          
          // Reset form
          addEmployeeForm.reset();
          
          // Optionally refresh the page or update the UI
          // window.location.reload();
        } else {
          // Error - show error message
          alert(`Error: ${result.error}`);
        }
      } catch (error) {
        console.error('Error submitting form:', error);
        alert('An error occurred while adding the facilitator. Please try again.');
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

  // Facilitator tab switching functionality
  const facilitatorTabs = document.querySelectorAll('.facilitator-nav-tab');
  const facilitatorOverview = document.getElementById('facilitatorOverview');
  const facilitatorDirectory = document.getElementById('facilitatorDirectory');

  facilitatorTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active class from all tabs
      facilitatorTabs.forEach(t => t.classList.remove('active'));
      // Add active class to clicked tab
      tab.classList.add('active');
      
      // Get the tab data attribute
      const tabName = tab.getAttribute('data-facilitator-tab');
      console.log(`Switched to ${tabName} tab`);
      
      // Show/hide content sections based on tab
      if (tabName === 'overview') {
        if (facilitatorOverview) facilitatorOverview.style.display = 'block';
        if (facilitatorDirectory) facilitatorDirectory.style.display = 'none';
      } else if (tabName === 'directory') {
        if (facilitatorOverview) facilitatorOverview.style.display = 'none';
        if (facilitatorDirectory) facilitatorDirectory.style.display = 'block';
      }
    });
  });

  // Search and filter functionality
  const searchInput = document.getElementById('facilitatorSearch');
  const departmentFilter = document.getElementById('departmentFilter');
  const levelFilter = document.getElementById('levelFilter');
  const statusFilter = document.getElementById('statusFilter');
  const facilitatorCards = document.querySelectorAll('.facilitator-card');
  const resultsCount = document.getElementById('resultsCount');

  function filterFacilitators() {
    const searchTerm = searchInput.value.toLowerCase();
    const departmentValue = departmentFilter.value;
    const levelValue = levelFilter.value;
    const statusValue = statusFilter.value;
    
    let visibleCount = 0;
    
    facilitatorCards.forEach(card => {
      const name = card.querySelector('.facilitator-name').textContent.toLowerCase();
      const role = card.querySelector('.facilitator-role').textContent.toLowerCase();
      const department = card.querySelector('.facilitator-department').textContent.toLowerCase();
      const experienceBadge = card.querySelector('.badge-experience').textContent.toLowerCase();
      const statusBadge = card.querySelector('.badge-status').textContent.toLowerCase();
      
      // Check search term
      const matchesSearch = searchTerm === '' || 
        name.includes(searchTerm) || 
        role.includes(searchTerm) ||
        department.includes(searchTerm);
      
      // Check filters
      const matchesDepartment = departmentValue === '' || department.includes(departmentValue);
      const matchesLevel = levelValue === '' || experienceBadge.includes(levelValue);
      const matchesStatus = statusValue === '' || statusBadge.includes(statusValue);
      
      if (matchesSearch && matchesDepartment && matchesLevel && matchesStatus) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });
    
    // Update results count
    if (resultsCount) {
      resultsCount.textContent = `Showing ${visibleCount} of ${facilitatorCards.length} facilitators`;
    }
  }

  // Add event listeners for search and filters
  if (searchInput) {
    searchInput.addEventListener('input', filterFacilitators);
  }
  if (departmentFilter) {
    departmentFilter.addEventListener('change', filterFacilitators);
  }
  if (levelFilter) {
    levelFilter.addEventListener('change', filterFacilitators);
  }
  if (statusFilter) {
    statusFilter.addEventListener('change', filterFacilitators);
  }

});
