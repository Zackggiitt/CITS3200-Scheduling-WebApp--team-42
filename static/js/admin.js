document.addEventListener('DOMContentLoaded', () => {
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
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      // Remove active class from all tabs
      tabs.forEach(t => t.classList.remove('active'));
      // Add active class to clicked tab
      tab.classList.add('active');
      
      // Get the tab data attribute
      const tabName = tab.getAttribute('data-tab');
      console.log(`Switched to ${tabName} tab`);
      
      // Here you can add logic to show/hide different content sections
      // For now, we'll just log the tab name
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
