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

});
