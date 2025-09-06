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
});
