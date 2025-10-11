document.addEventListener('DOMContentLoaded', () => {
  console.log('Admin dashboard loaded');

  const notifBtn = document.getElementById('adminNotifBtn');
  if (notifBtn) {
    notifBtn.addEventListener('click', () => {
      const badge = notifBtn.querySelector('.notif-badge');
      if (badge) {
        // Example behavior: mark notifications as read (hide badge)
        badge.remove();
      }
    });
  }

  // Tab switching functionality
  const tabs = document.querySelectorAll('.admin-tab');
  const facilitatorManagement = document.querySelector('.facilitator-management');
  const scheduleManagement = document.querySelector('.schedule-management');
  const unitStatusCard = document.querySelector('.unit-status-card');
  const welcomeBanner = document.querySelector('.admin-welcome-banner');

  // Helper: show the correct tab and content
  function showTab(tabName) {
    // Remove active class from all tabs
    tabs.forEach(t => t.classList.remove('active'));

    if (tabName === 'employees') {
      const employeesTab = document.querySelector('.admin-tab[data-tab="employees"]');
      if (employeesTab) employeesTab.classList.add('active');
      if (welcomeBanner) welcomeBanner.style.display = 'none';
      if (unitStatusCard) unitStatusCard.style.display = 'none';
      if (facilitatorManagement) facilitatorManagement.style.display = 'block';
      if (scheduleManagement) scheduleManagement.style.display = 'none';
      console.log('Employees tab activated');
    } else if (tabName === 'schedule') {
      const scheduleTab = document.querySelector('.admin-tab[data-tab="schedule"]');
      if (scheduleTab) scheduleTab.classList.add('active');
      if (welcomeBanner) welcomeBanner.style.display = 'none';
      if (unitStatusCard) unitStatusCard.style.display = 'none';
      if (facilitatorManagement) facilitatorManagement.style.display = 'none';
      if (scheduleManagement) scheduleManagement.style.display = 'block';
      console.log('Schedule tab activated');
      // Initialize schedule management when switching to schedule tab
      setTimeout(initializeScheduleManagement, 100);
    } else {
      const dashboardTab = document.querySelector('.admin-tab[data-tab="dashboard"]');
      if (dashboardTab) dashboardTab.classList.add('active');
      if (welcomeBanner) welcomeBanner.style.display = 'block';
      if (unitStatusCard) unitStatusCard.style.display = 'block';
      if (facilitatorManagement) facilitatorManagement.style.display = 'none';
      if (scheduleManagement) scheduleManagement.style.display = 'none';
      console.log('Dashboard tab activated');
    }
  }

  // Initialize dashboard state on page load
  function initializeDashboard() {
    console.log('Initializing dashboard state...');
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab');
    if (activeTab === 'employees') {
      showTab('employees');
    } else if (activeTab === 'schedule') {
      showTab('schedule');
      // Initialize schedule management when schedule tab is active
      setTimeout(initializeScheduleManagement, 100);
    } else {
      showTab('dashboard');
    }
  }

  // Initialize on page load
  initializeDashboard();

  // Tab click handler
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.getAttribute('data-tab');
      console.log(`Switched to ${tabName} tab`);
      showTab(tabName);
    });
  });

  // Settings button functionality
  const settingsBtn = document.querySelector('.admin-settings-btn');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      console.log('Settings button clicked');
      alert('Settings panel coming soon!');
    });
  }

  // Modal functionality (Add Employee)
  const modal = document.getElementById('addEmployeeModal');
  const closeModalBtn = document.getElementById('closeModal');
  const cancelBtn = document.getElementById('cancelBtn');
  const addEmployeeForm = document.getElementById('addEmployeeForm');

  // Show modal when Add Employee button is clicked (event delegation)
  document.addEventListener('click', (e) => {
    if (e.target.closest('.facilitator-action-btn.primary')) {
      e.preventDefault();
      console.log('Add Employee button clicked!');
      if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
      }
    }
  });

  // Hide modal (close)
  if (closeModalBtn && modal) {
    closeModalBtn.addEventListener('click', () => {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  // Hide modal (cancel)
  if (cancelBtn && modal) {
    cancelBtn.addEventListener('click', () => {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  // Hide modal when clicking outside
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  }

  // Handle add employee form
  if (addEmployeeForm) {
    addEmployeeForm.addEventListener('submit', async (e) => {
      e.preventDefault();

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

      const submitBtn = addEmployeeForm.querySelector('.btn-primary');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Adding...';
      submitBtn.disabled = true;

      try {
        const response = await fetch('/admin/create-employee', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
          },
          body: JSON.stringify(employeeData)
        });

        const result = await response.json();

        if (result.success) {
          alert('Employee added successfully! They will receive login credentials via email.');
          modal.style.display = 'none';
          document.body.style.overflow = 'auto';
          addEmployeeForm.reset();
          // Stay on employees tab after addition
          window.location.href = '/admin/dashboard?tab=employees';
        } else {
          alert(`Error: ${result.error}`);
        }
      } catch (error) {
        console.error('Error submitting form:', error);
        alert('An error occurred while adding the employee. Please try again.');
      } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Close Add modal with Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  });

  // Edit Employee Modal functionality
  const editModal = document.getElementById('editEmployeeModal');
  const closeEditModalBtn = document.getElementById('closeEditModal');
  const cancelEditBtn = document.getElementById('cancelEditBtn');
  const editEmployeeForm = document.getElementById('editEmployeeForm');

  if (closeEditModalBtn && editModal) {
    closeEditModalBtn.addEventListener('click', () => {
      editModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  if (cancelEditBtn && editModal) {
    cancelEditBtn.addEventListener('click', () => {
      editModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  if (editModal) {
    editModal.addEventListener('click', (e) => {
      if (e.target === editModal) {
        editModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  }

  // Handle edit employee form
  if (editEmployeeForm) {
    editEmployeeForm.addEventListener('submit', async (e) => {
      e.preventDefault();

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

      const submitBtn = editEmployeeForm.querySelector('.btn-primary');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Updating...';
      submitBtn.disabled = true;

      try {
        const response = await fetch('/admin/update-employee', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
          },
          body: JSON.stringify(employeeData)
        });

        const result = await response.json();

        if (result.success) {
          alert('Employee details updated successfully!');
          editModal.style.display = 'none';
          document.body.style.overflow = 'auto';
          updateEmployeeCardInPlace(employeeData);
        } else {
          alert(`Error: ${result.error}`);
        }
      } catch (error) {
        console.error('Error updating employee:', error);
        alert('An error occurred while updating the employee. Please try again.');
      } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Close Edit modal with Escape
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

    facilitatorCards.forEach(card => {
      const name = card.querySelector('.facilitator-name').textContent.toLowerCase();
      const email = card.querySelector('.facilitator-email').textContent.toLowerCase();
      const positionBadge = card.querySelector('.badge-position') ? card.querySelector('.badge-position').textContent.toLowerCase() : '';
      const statusBadge = card.querySelector('.badge-status').textContent.toLowerCase();

      const matchesSearch = searchTerm === '' || name.includes(searchTerm) || email.includes(searchTerm);

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

      let matchesStatus = true;
      if (statusValue !== '') {
        // Normalize both the filter value and badge text for comparison
        const normalizedFilterValue = statusValue.replace('_', ' ').toLowerCase();
        const normalizedBadgeText = statusBadge.replace('_', ' ').toLowerCase();
        matchesStatus = normalizedBadgeText.includes(normalizedFilterValue);
      }

      if (matchesSearch && matchesPosition && matchesStatus) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });

    updateResultsCount();
  }

  // Add event listeners for search and filters
  if (searchInput) searchInput.addEventListener('input', filterFacilitators);
  if (positionFilter) positionFilter.addEventListener('change', filterFacilitators);
  if (statusFilter) statusFilter.addEventListener('change', filterFacilitators);

  // Conditional Role dropdown (Add)
  const positionSelect = document.getElementById('position');
  const roleGroup = document.getElementById('roleGroup');
  const roleSelect = document.getElementById('role');

  function toggleRoleDropdown() {
    const selectedPosition = positionSelect.value;

    if (selectedPosition === 'facilitator') {
      roleGroup.style.display = 'block';
      roleSelect.setAttribute('required', 'required');
      roleSelect.value = 'lab_facilitator';
    } else {
      roleGroup.style.display = 'none';
      roleSelect.removeAttribute('required');
      roleSelect.value = '';
    }
  }

  if (positionSelect) {
    positionSelect.addEventListener('change', toggleRoleDropdown);
  }

  // Conditional Role dropdown (Edit)
  const editPositionSelect = document.getElementById('editPosition');
  const editRoleGroup = document.getElementById('editRoleGroup');
  const editRoleSelect = document.getElementById('editRole');

  function toggleEditRoleDropdown() {
    const selectedPosition = editPositionSelect.value;

    if (selectedPosition === 'facilitator') {
      editRoleGroup.style.display = 'block';
      editRoleSelect.setAttribute('required', 'required');
      editRoleSelect.value = 'lab_facilitator';
    } else {
      editRoleGroup.style.display = 'none';
      editRoleSelect.removeAttribute('required');
      editRoleSelect.value = '';
    }
  }

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

  // Schedule Management Functionality
  const scheduleSearchInput = document.getElementById('scheduleSearch');
  const scheduleStatusFilter = document.getElementById('statusFilter');
  const scheduleSemesterFilter = document.getElementById('semesterFilter');
  const unitScheduleList = document.getElementById('unitScheduleList');
  const scheduleResultsCount = document.getElementById('scheduleResultsCount');

  // Global variable to store all units
  let allUnits = [];
  let filteredUnits = [];

  // Initialize schedule management when page loads
  function initializeScheduleManagement() {
    if (window.unitsData) {
      allUnits = window.unitsData;
      filteredUnits = [...allUnits];
      renderUnits();
      updateScheduleResultsCount();
    }
  }

  // Render units to the DOM
  function renderUnits() {
    if (!unitScheduleList) return;

    if (filteredUnits.length === 0) {
      unitScheduleList.innerHTML = `
        <div class="empty-state">
          <span class="material-icons">event</span>
          <h3>No units found</h3>
          <p>No units match your current search and filter criteria.</p>
        </div>
      `;
      return;
    }

    unitScheduleList.innerHTML = filteredUnits.map(unit => {
      const scheduleStatus = unit.schedule_status || 'draft';
      const statusClass = scheduleStatus === 'published' ? 'published' : scheduleStatus === 'unpublished' ? 'unpublished' : 'draft';
      const coordinatorName = unit.creator ? unit.creator.full_name : 'Unknown Coordinator';
      const startDate = unit.start_date ? new Date(unit.start_date).toLocaleDateString('en-GB') : 'Not set';
      const endDate = unit.end_date ? new Date(unit.end_date).toLocaleDateString('en-GB') : 'Not set';
      const publishedDate = unit.published_at ? new Date(unit.published_at).toLocaleString('en-GB') : null;
      const unpublishedDate = unit.unpublished_at ? new Date(unit.unpublished_at).toLocaleString('en-GB') : null;

      return `
        <div class="unit-schedule-card" data-unit-id="${unit.id}">
          <div class="unit-schedule-info">
            <div class="unit-schedule-header">
              <h3 class="unit-schedule-name">${unit.unit_code} - ${unit.unit_name}</h3>
              <div class="unit-schedule-badges">
                <span class="badge badge-semester">${unit.semester} ${unit.year}</span>
                <span class="badge badge-status badge-${statusClass}">
                  ${scheduleStatus.charAt(0).toUpperCase() + scheduleStatus.slice(1)}
                </span>
              </div>
            </div>
            <div class="unit-schedule-details">
              <div class="unit-schedule-meta">
                <span class="unit-schedule-coordinator">
                  <span class="material-icons">person</span>
                  ${coordinatorName}
                </span>
                <span class="unit-schedule-dates">
                  <span class="material-icons">calendar_today</span>
                  ${startDate} - ${endDate}
                </span>
              </div>
              <div class="unit-schedule-stats">
                <span class="unit-schedule-stat">
                  <span class="material-icons">event</span>
                  ${unit.modules ? unit.modules.length : 0} modules
                </span>
                ${publishedDate ? `
                <span class="unit-schedule-stat">
                  <span class="material-icons">publish</span>
                  Published ${publishedDate}
                </span>
                ` : ''}
                ${unpublishedDate ? `
                <span class="unit-schedule-stat">
                  <span class="material-icons">unpublish</span>
                  Unpublished ${unpublishedDate}
                </span>
                ` : ''}
              </div>
            </div>
          </div>
          <div class="unit-schedule-actions">
            ${scheduleStatus === 'published' ? `
            <button class="action-btn unpublish" title="Unpublish Schedule" onclick="openUnpublishModal(${unit.id}, '${unit.unit_code}', '${coordinatorName}')">
              <span class="material-icons">unpublish</span>
              <span>Unpublish</span>
            </button>
            ` : ''}
            <button class="action-btn view" title="View Schedule" onclick="viewUnitSchedule(${unit.id})">
              <span class="material-icons">visibility</span>
              <span>View</span>
            </button>
            <button class="action-btn history" title="Version History" onclick="viewVersionHistory(${unit.id})">
              <span class="material-icons">history</span>
              <span>History</span>
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  function filterScheduleUnits() {
    if (!scheduleSearchInput || !scheduleStatusFilter || !scheduleSemesterFilter) return;

    const searchTerm = scheduleSearchInput.value.toLowerCase();
    const statusValue = scheduleStatusFilter.value;
    const semesterValue = scheduleSemesterFilter.value;

    filteredUnits = allUnits.filter(unit => {
      // Search filter
      const matchesSearch = searchTerm === '' || 
        unit.unit_code.toLowerCase().includes(searchTerm) ||
        unit.unit_name.toLowerCase().includes(searchTerm);

      // Status filter
      let matchesStatus = true;
      if (statusValue !== '') {
        const unitStatus = unit.schedule_status || 'draft';
        matchesStatus = unitStatus === statusValue;
      }

      // Semester filter
      let matchesSemester = true;
      if (semesterValue !== '') {
        matchesSemester = unit.semester.toLowerCase().includes(semesterValue.toLowerCase());
      }

      return matchesSearch && matchesStatus && matchesSemester;
    });

    renderUnits();
    updateScheduleResultsCount();
  }

  // Add event listeners for schedule search and filters
  if (scheduleSearchInput) scheduleSearchInput.addEventListener('input', filterScheduleUnits);
  if (scheduleStatusFilter) scheduleStatusFilter.addEventListener('change', filterScheduleUnits);
  if (scheduleSemesterFilter) scheduleSemesterFilter.addEventListener('change', filterScheduleUnits);

  // Initialize schedule management when dashboard loads
  initializeScheduleManagement();

  // Unpublish Modal functionality
  const unpublishModal = document.getElementById('unpublishModal');
  const closeUnpublishModalBtn = document.getElementById('closeUnpublishModal');
  const cancelUnpublishBtn = document.getElementById('cancelUnpublishBtn');
  const unpublishForm = document.getElementById('unpublishForm');

  if (closeUnpublishModalBtn && unpublishModal) {
    closeUnpublishModalBtn.addEventListener('click', () => {
      unpublishModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  if (cancelUnpublishBtn && unpublishModal) {
    cancelUnpublishBtn.addEventListener('click', () => {
      unpublishModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  if (unpublishModal) {
    unpublishModal.addEventListener('click', (e) => {
      if (e.target === unpublishModal) {
        unpublishModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  }

  // Handle unpublish form
  if (unpublishForm) {
    unpublishForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const formData = new FormData(unpublishForm);
      const unpublishData = {
        unitId: formData.get('unitId'),
        reason: formData.get('reason'),
        notifyCoordinator: formData.get('notifyCoordinator') === 'on',
        notifyFacilitators: formData.get('notifyFacilitators') === 'on'
      };

      console.log('Submitting unpublish data:', unpublishData);

      const submitBtn = unpublishForm.querySelector('.btn-warning');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Unpublishing...';
      submitBtn.disabled = true;

      try {
        const response = await fetch('/admin/unpublish-schedule', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
          },
          body: JSON.stringify(unpublishData)
        });

        const result = await response.json();

        if (result.success) {
          alert(result.message);
          unpublishModal.style.display = 'none';
          document.body.style.overflow = 'auto';
          unpublishForm.reset();
          // Refresh the page to show updated status
          window.location.reload();
        } else {
          alert(`Error: ${result.error}`);
        }
      } catch (error) {
        console.error('Error unpublishing schedule:', error);
        alert('An error occurred while unpublishing the schedule. Please try again.');
      } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Close Unpublish modal with Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && unpublishModal && unpublishModal.style.display === 'flex') {
      unpublishModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  });

  // Version History Modal functionality
  const versionHistoryModal = document.getElementById('versionHistoryModal');
  const closeVersionHistoryModalBtn = document.getElementById('closeVersionHistoryModal');
  const closeVersionHistoryBtn = document.getElementById('closeVersionHistoryBtn');

  if (closeVersionHistoryModalBtn && versionHistoryModal) {
    closeVersionHistoryModalBtn.addEventListener('click', () => {
      versionHistoryModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  if (closeVersionHistoryBtn && versionHistoryModal) {
    closeVersionHistoryBtn.addEventListener('click', () => {
      versionHistoryModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    });
  }

  if (versionHistoryModal) {
    versionHistoryModal.addEventListener('click', (e) => {
      if (e.target === versionHistoryModal) {
        versionHistoryModal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  }

  // Close Version History modal with Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && versionHistoryModal && versionHistoryModal.style.display === 'flex') {
      versionHistoryModal.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  });

});

// Dropdown functionality (global)
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
    console.log(`Disabling account for facilitator ID: ${facilitatorId}`);
    alert(`${facilitatorName}'s account has been disabled.`);
    document.getElementById(`dropdown-${facilitatorId}`).style.display = 'none';
  }
}

// Delete account function
async function deleteAccount(facilitatorId, facilitatorName) {
  console.log(`Attempting to delete facilitator ID: ${facilitatorId}, Name: ${facilitatorName}`);

  if (confirm(`Are you sure you want to permanently delete ${facilitatorName}'s account? This action cannot be undone.`)) {
    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      console.log('CSRF Token:', csrfToken);

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
        const facilitatorCard = document.querySelector(`.facilitator-card[data-facilitator-id="${facilitatorId}"]`);
        if (facilitatorCard) {
          facilitatorCard.remove();
        }

        updateResultsCount();
        alert(`${facilitatorName}'s employee account has been deleted successfully.`);
      } else {
        alert(`Error: ${result.message || 'Failed to delete account'}`);
      }
    } catch (error) {
      console.error('Error deleting facilitator:', error);
      alert('An error occurred while deleting the account. Please try again.');
    }

    document.getElementById(`dropdown-${facilitatorId}`).style.display = 'none';
  }
}

// Unified results count updater
function updateResultsCount() {
  const resultsCountEl = document.getElementById('resultsCount');
  if (!resultsCountEl) return;
  const allCards = Array.from(document.querySelectorAll('.facilitator-card'));
  const visibleCards = allCards.filter(c => c.style.display !== 'none');
  resultsCountEl.textContent = `Showing ${visibleCards.length} of ${allCards.length} employees`;
}

// Open edit modal function
function openEditModal(facilitatorId, facilitatorName, facilitatorEmail) {
  console.log(`Opening edit modal for employee ID: ${facilitatorId}, Name: ${facilitatorName}`);

  document.getElementById('editEmployeeId').value = facilitatorId;
  document.getElementById('editEmail').value = facilitatorEmail;
  document.getElementById('editFullName').value = facilitatorName;

  const employeeCard = document.querySelector(`.facilitator-card[data-facilitator-id="${facilitatorId}"]`);
  if (employeeCard) {
    const phoneElement = employeeCard.querySelector('.facilitator-phone');
    if (phoneElement) {
      document.getElementById('editPhone').value = phoneElement.textContent.trim();
    }

    const positionElement = employeeCard.querySelector('.badge-position');
    if (positionElement) {
      const positionText = positionElement.textContent.trim();
      let positionValue = '';
      if (positionText.toLowerCase().includes('facilitator')) {
        positionValue = 'facilitator';
      } else if (positionText.toLowerCase().includes('unit') && positionText.toLowerCase().includes('coordinator')) {
        positionValue = 'unit_coordinator';
      } else if (positionText.toLowerCase().includes('admin')) {
        positionValue = 'admin';
      }
      document.getElementById('editPosition').value = positionValue;

      if (positionValue === 'facilitator') {
        const roleElement = employeeCard.querySelector('.badge-role');
        if (roleElement) {
          const roleText = roleElement.textContent.trim();
          let roleValue = '';
          if (roleText.toLowerCase().includes('lab')) roleValue = 'lab_facilitator';
          else if (roleText.toLowerCase().includes('senior')) roleValue = 'senior_facilitator';
          else if (roleText.toLowerCase().includes('lead')) roleValue = 'lead_facilitator';

          document.getElementById('editRoleGroup').style.display = 'block';
          document.getElementById('editRole').value = roleValue;
          document.getElementById('editRole').setAttribute('required', 'required');
        }
      } else {
        document.getElementById('editRoleGroup').style.display = 'none';
        document.getElementById('editRole').removeAttribute('required');
      }
    }

    const statusElement = employeeCard.querySelector('.badge-status');
    if (statusElement) {
      const statusText = statusElement.textContent.trim();
      let statusValue = '';
      if (statusText.toLowerCase().includes('active')) statusValue = 'active';
      else if (statusText.toLowerCase().includes('inactive')) statusValue = 'inactive';
      else if (statusText.toLowerCase().includes('leave')) statusValue = 'on_leave';
      else statusValue = 'active';
      document.getElementById('editStatus').value = statusValue;
    } else {
      document.getElementById('editStatus').value = 'active';
    }
  }

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

// Update employee card in place without redirecting
function updateEmployeeCardInPlace(employeeData) {
  const employeeId = employeeData.employeeId;
  const employeeCard = document.querySelector(`.facilitator-card[data-facilitator-id="${employeeId}"]`);

  if (employeeCard) {
    const nameElement = employeeCard.querySelector('.facilitator-name');
    if (nameElement) nameElement.textContent = employeeData.fullName;

    const emailElement = employeeCard.querySelector('.facilitator-email');
    if (emailElement) emailElement.textContent = employeeData.email;

    const positionBadge = employeeCard.querySelector('.badge-position');
    if (positionBadge) {
      const positionText = employeeData.position.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      positionBadge.textContent = positionText;
    }

    const statusBadge = employeeCard.querySelector('.badge-status');
    if (statusBadge) {
      const statusText = employeeData.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      statusBadge.textContent = statusText;
    }

    if (employeeData.position === 'facilitator' && employeeData.role) {
      let roleBadge = employeeCard.querySelector('.badge-role');
      if (!roleBadge) {
        const badgesContainer = employeeCard.querySelector('.facilitator-badges');
        if (badgesContainer) {
          roleBadge = document.createElement('span');
          roleBadge.className = 'badge badge-role';
          badgesContainer.appendChild(roleBadge);
        }
      }
      if (roleBadge) {
        const roleText = employeeData.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        roleBadge.textContent = roleText;
      }
    } else {
      const roleBadge = employeeCard.querySelector('.badge-role');
      if (roleBadge) roleBadge.remove();
    }

    const phoneElement = employeeCard.querySelector('.facilitator-phone');
    if (phoneElement) phoneElement.textContent = employeeData.phone;

    console.log('Employee card updated in place successfully');
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

  const newPassword = prompt(`Enter new password for ${employeeName}:`);
  if (!newPassword) return;
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

// Schedule Management Global Functions

// Open unpublish modal function
function openUnpublishModal(unitId, unitCode, coordinatorName) {
  console.log(`Opening unpublish modal for unit ID: ${unitId}, Code: ${unitCode}`);
  
  document.getElementById('unpublishUnitId').value = unitId;
  document.getElementById('unpublishUnitCode').textContent = unitCode;
  document.getElementById('unpublishUnitCoordinator').textContent = coordinatorName;
  
  const unpublishModal = document.getElementById('unpublishModal');
  if (unpublishModal) {
    unpublishModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

// View unit schedule function
function viewUnitSchedule(unitId) {
  console.log(`Viewing schedule for unit ID: ${unitId}`);
  // TODO: Implement view schedule functionality
  alert(`View schedule functionality for unit ${unitId} will be implemented.`);
}

// View version history function
async function viewVersionHistory(unitId) {
  console.log(`Viewing version history for unit ID: ${unitId}`);
  
  try {
    const response = await fetch(`/admin/version-history/${unitId}`, {
      method: 'GET',
      headers: {
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
      }
    });

    const result = await response.json();

    if (result.success) {
      displayVersionHistory(result.version_history, result.unit_code);
    } else {
      alert(`Error: ${result.error}`);
    }
  } catch (error) {
    console.error('Error fetching version history:', error);
    alert('An error occurred while fetching version history. Please try again.');
  }
}

// Display version history in modal
function displayVersionHistory(versionHistory, unitCode) {
  const versionHistoryList = document.getElementById('versionHistoryList');
  
  if (!versionHistory || versionHistory.length === 0) {
    versionHistoryList.innerHTML = `
      <div class="empty-version-history">
        <span class="material-icons">history</span>
        <h3>No Version History</h3>
        <p>No version history available for ${unitCode}.</p>
      </div>
    `;
  } else {
    versionHistoryList.innerHTML = versionHistory.map(version => `
      <div class="version-history-item">
        <div class="version-header">
          <span class="version-number">Version ${version.version}</span>
          <span class="version-status status-${version.status}">${version.status.charAt(0).toUpperCase() + version.status.slice(1)}</span>
        </div>
        <div class="version-details">
          <div class="version-date">
            <span class="material-icons">schedule</span>
            <span>${new Date(version.created_at).toLocaleString()}</span>
          </div>
          ${version.published_at ? `
            <div class="version-published">
              <span class="material-icons">publish</span>
              <span>Published: ${new Date(version.published_at).toLocaleString()}</span>
            </div>
          ` : ''}
          ${version.unpublished_at ? `
            <div class="version-unpublished">
              <span class="material-icons">unpublish</span>
              <span>Unpublished: ${new Date(version.unpublished_at).toLocaleString()}</span>
            </div>
            <div class="version-reason">
              <span class="material-icons">info</span>
              <span><strong>Reason:</strong> ${version.unpublish_reason}</span>
            </div>
            <div class="version-admin">
              <span class="material-icons">person</span>
              <span><strong>Unpublished by:</strong> ${version.unpublished_by}</span>
            </div>
          ` : ''}
        </div>
      </div>
    `).join('');
  }
  
  const versionHistoryModal = document.getElementById('versionHistoryModal');
  if (versionHistoryModal) {
    versionHistoryModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

// Update schedule results count
function updateScheduleResultsCount() {
  const resultsCountEl = document.getElementById('scheduleResultsCount');
  if (!resultsCountEl) return;
  resultsCountEl.textContent = `Showing ${filteredUnits.length} of ${allUnits.length} units`;
}