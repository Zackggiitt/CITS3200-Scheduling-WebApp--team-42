// Navigation between dashboard, calendar, and notifications
document.addEventListener('DOMContentLoaded', function() {
    const dashboardSections = document.querySelectorAll('#welcome, #alert, #stats, #details');
    const calendarView = document.getElementById('calendar-view');
    const availabilityView = document.getElementById('availability-view');
    const navItems = document.querySelectorAll('.dashboard-nav-item');
    
    // Notification popup elements
    const bellIcon = document.getElementById('bell-icon');
    const notificationPopup = document.getElementById('notification-popup');
    const popupOverlay = document.getElementById('popup-overlay');
    const headerNotificationBadge = document.getElementById('header-notification-badge');
    const popupCloseBtn = document.getElementById('popup-close');
    
    // Navigation click handlers
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            // Show/hide sections
            const href = this.getAttribute('href');

            if (href === '#availability') {
                // Show availability view
                dashboardSections.forEach(section => section.style.display = 'none');
                availabilityView.style.display = 'block';
                calendarView.style.display = 'none';
            } else if (href === '#schedule') {
                // Show calendar view
                dashboardSections.forEach(section => section.style.display = 'none');
                availabilityView.style.display = 'none';
                calendarView.style.display = 'block';
                initCalendar();
            } else {
                // Show dashboard view
                dashboardSections.forEach(section => section.style.display = 'block');
                availabilityView.style.display = 'none';
                calendarView.style.display = 'none';
            }
        });
    });

    // Notification popup functionality
    function showNotificationPopup() {
        notificationPopup.style.display = 'block';
        popupOverlay.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    function hideNotificationPopup() {
        notificationPopup.style.display = 'none';
        popupOverlay.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    // Bell icon click handler
    if (bellIcon) {
        bellIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            showNotificationPopup();
        });
    }

    // Close button handler
    if (popupCloseBtn) {
        popupCloseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            hideNotificationPopup();
        });
    }

    // Escape key closes popup
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && notificationPopup && notificationPopup.style.display === 'block') {
            hideNotificationPopup();
        }
    });

    // Overlay click handler to close popup
    if (popupOverlay) {
        popupOverlay.addEventListener('click', function() {
            hideNotificationPopup();
        });
    }

    // Close popup when clicking outside
    document.addEventListener('click', function(e) {
        if (notificationPopup && notificationPopup.style.display === 'block') {
            if (!notificationPopup.contains(e.target) && !bellIcon.contains(e.target)) {
                hideNotificationPopup();
            }
        }
    });

    // Popup filter functionality
    const popupFilterBtns = document.querySelectorAll('.popup-filter-btn');
    const popupNotificationItems = document.querySelectorAll('.popup-notification-item');

    popupFilterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active filter
            popupFilterBtns.forEach(f => f.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            
            // Filter notifications
            popupNotificationItems.forEach(item => {
                if (filter === 'all') {
                    item.style.display = 'flex';
                } else if (filter === 'unread' && item.classList.contains('unread')) {
                    item.style.display = 'flex';
                } else if (filter === 'action' && item.querySelector('.popup-action-btn')) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    // Mark all as read in popup
    const popupMarkAllReadBtn = document.getElementById('popup-mark-all-read');
    if (popupMarkAllReadBtn) {
        popupMarkAllReadBtn.addEventListener('click', function() {
            const unreadItems = document.querySelectorAll('.popup-notification-item.unread');
            unreadItems.forEach(item => {
                item.classList.remove('unread');
            });
            
            // Update notification badge
            updateHeaderNotificationBadge();
        });
    }

    // Popup action buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.popup-action-btn.accept')) {
            const notification = e.target.closest('.popup-notification-item');
            notification.classList.remove('unread');
            updateHeaderNotificationBadge();
            alert('Shift accepted successfully!');
        } else if (e.target.closest('.popup-action-btn.decline')) {
            const notification = e.target.closest('.popup-notification-item');
            notification.classList.remove('unread');
            notification.style.display = 'none';
            updateHeaderNotificationBadge();
            alert('Shift declined.');
        } else if (e.target.closest('.popup-action-btn.primary')) {
            // Handle "Update Now" button
            hideNotificationPopup();
            // Navigate to availability section
            const availabilityNavItem = document.querySelector('a[href="#availability"]');
            if (availabilityNavItem) {
                availabilityNavItem.click();
            }
        }
    });

    // View all notifications button
    const viewAllBtn = document.getElementById('view-all-notifications');
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', function() {
            hideNotificationPopup();
            // You can implement a full notifications page here if needed
            alert('View all notifications functionality can be implemented here.');
        });
    }

    // Function to update header notification badge
    function updateHeaderNotificationBadge() {
        const unreadCount = document.querySelectorAll('.popup-notification-item.unread').length;
        
        if (unreadCount === 0) {
            headerNotificationBadge.style.display = 'none';
        } else {
            headerNotificationBadge.style.display = 'flex';
            headerNotificationBadge.textContent = unreadCount;
        }
    }

    // Update greeting icon based on time of day
    function updateGreetingIcon() {
        const now = new Date();
        const hour = now.getHours();
        const iconElement = document.querySelector('.welcome-icon-wrapper .material-icons');
        
        if (iconElement) {
            if (hour >= 5 && hour < 12) {
                // Morning (5 AM - 11:59 AM)
                iconElement.textContent = 'wb_sunny';
            } else if (hour >= 12 && hour < 17) {
                // Afternoon (12 PM - 4:59 PM)
                iconElement.textContent = 'wb_sunny';
            } else {
                // Night (9 PM - 4:59 AM)
                iconElement.textContent = 'nights_stay';
            }
        }
    }

    // Call the function when page loads
    updateGreetingIcon();
    updateAvailableDaysCounter();

    // Calendar functionality
    let currentDate = new Date();
    const monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"];
    
    function initCalendar() {
        updateCalendarHeader();
        generateCalendarDays();
    }
    
    function updateCalendarHeader() {
        const monthTitle = document.getElementById('current-month');
        if (monthTitle) {
            monthTitle.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
        }
    }
    
    function generateCalendarDays() {
        const calendarDays = document.getElementById('calendar-days');
        if (!calendarDays) return;
        
        calendarDays.innerHTML = '';
        
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        
        // First day of the month and how many days in month
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDayOfWeek = firstDay.getDay();
        
        // Previous month's trailing days
        const prevMonth = new Date(year, month, 0);
        const daysInPrevMonth = prevMonth.getDate();
        
        for (let i = startingDayOfWeek - 1; i >= 0; i--) {
            const dayElement = createDayElement(daysInPrevMonth - i, true);
            calendarDays.appendChild(dayElement);
        }
        
        // Current month days
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = createDayElement(day, false);
            calendarDays.appendChild(dayElement);
        }
        
        // Next month's leading days
        const totalCells = calendarDays.children.length;
        const remainingCells = 42 - totalCells; // 6 rows × 7 days
        
        for (let day = 1; day <= remainingCells; day++) {
            const dayElement = createDayElement(day, true);
            calendarDays.appendChild(dayElement);
        }
    }
    
    function createDayElement(dayNumber, isOtherMonth) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        if (isOtherMonth) {
            dayElement.classList.add('other-month');
        }
        
        // Check if it's today
        const today = new Date();
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        
        if (!isOtherMonth && 
            dayNumber === today.getDate() && 
            month === today.getMonth() && 
            year === today.getFullYear()) {
            dayElement.classList.add('today');
        }
        
        dayElement.innerHTML = `
            <div class="day-number">${dayNumber}</div>
            <div class="day-events">
                ${generateEvents(dayNumber, isOtherMonth)}
            </div>
        `;
        
        return dayElement;
    }
    
    function generateEvents(dayNumber, isOtherMonth) {
        if (isOtherMonth) return '';
        
        // Sample events (replace with real data)
        const events = [];
        
        if (dayNumber === 22) { // Today
            events.push('<div class="event confirmed">Lab Session 9-5</div>');
        }
        if (dayNumber === 23) { // Tomorrow
            events.push('<div class="event pending">Lab Session 9-5</div>');
        }
        if (dayNumber === 25) {
            events.push('<div class="event available">Available</div>');
        }
        if (dayNumber === 28) {
            events.push('<div class="event confirmed">Lab Session 2-6</div>');
        }
        
        return events.join('');
    }
    
    // Month navigation
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    
    if (prevMonthBtn) {
        prevMonthBtn.addEventListener('click', function() {
            currentDate.setMonth(currentDate.getMonth() - 1);
            updateCalendarHeader();
            generateCalendarDays();
        });
    }
    
    if (nextMonthBtn) {
        nextMonthBtn.addEventListener('click', function() {
            currentDate.setMonth(currentDate.getMonth() + 1);
            updateCalendarHeader();
            generateCalendarDays();
        });
    }

    // GLOBAL CLICK HANDLER - Only one for all click events
    document.addEventListener('click', function(e) {
        // Handle notification accept/decline buttons (legacy support)
        if (e.target.closest('.action-btn.accept')) {
            const notification = e.target.closest('.notification-item');
            notification.classList.remove('unread');
            updateNotificationBadge();
            alert('Shift accepted successfully!');
        } else if (e.target.closest('.action-btn.decline')) {
            const notification = e.target.closest('.notification-item');
            notification.classList.remove('unread');
            notification.style.display = 'none';
            updateNotificationBadge();
            alert('Shift declined.');
        }
        
        // Handle update availability button
        else if (e.target.classList.contains('update-btn')) {
            // Collect all availability data
            const availability = [];
            document.querySelectorAll('.day-checkbox').forEach(checkbox => {
                const dayRow = checkbox.closest('.day-row');
                const dayName = checkbox.getAttribute('data-day');
                const isAvailable = checkbox.checked;
                
                if (isAvailable) {
                    const timeInputs = dayRow.querySelectorAll('.time-input');
                    const startTime = timeInputs[0] ? timeInputs[0].value : '';
                    const endTime = timeInputs[1] ? timeInputs[1].value : '';
                    availability.push({
                        day: dayName,
                        available: true,
                        startTime: startTime,
                        endTime: endTime
                    });
                } else {
                    availability.push({
                        day: dayName,
                        available: false
                    });
                }
            });
            
            console.log('Saving availability:', availability);
            alert('All up to date!');

            // Update the alert box message and icon
            const alertContent = document.querySelector('.alert-content p');
            const alertIcon = document.querySelector('.alert-content .material-icons');

            if (alertContent) {
                alertContent.innerHTML = '<strong>All up to date!</strong> Your availability has been successfully updated.';
            }

            if (alertIcon) {
                alertIcon.textContent = 'checklist';
            }

            // Change alert styling to success
            const alertBar = document.querySelector('.alert-bar');
            if (alertBar) {
                alertBar.style.backgroundColor = '#d1fae5';
                alertBar.style.borderColor = '#10b981';
                alertBar.style.color = '#065f46';
            }

            // Hide the "Update Now" button
            const updateBtn = document.getElementById('update-now-btn');
            if (updateBtn) {
                updateBtn.style.display = 'none';
            }
        }
        
        // Handle "Update Now" button in alert section
        else if (e.target.closest('#update-now-btn')) {
            e.preventDefault();
            
            // Remove active state from all nav items
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active state to availability tab
            const availabilityNavItem = document.querySelector('a[href="#availability"]');
            if (availabilityNavItem) {
                availabilityNavItem.classList.add('active');
            }
            
            // Hide all sections and show availability
            dashboardSections.forEach(section => section.style.display = 'none');
            availabilityView.style.display = 'block';
            calendarView.style.display = 'none';
        }
    });

    // AVAILABILITY TOGGLE FUNCTIONALITY
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('day-checkbox')) {
            const dayRow = e.target.closest('.day-row');
            const timeInputs = dayRow.querySelector('.time-inputs');
            
            if (e.target.checked) {
                // Show time inputs when toggle is ON
                timeInputs.classList.remove('disabled');
                timeInputs.innerHTML = `
                    <input type="time" class="time-input" value="08:00">
                    <span class="time-separator">to</span>
                    <input type="time" class="time-input" value="18:00">
                `;
            } else {
                // Show "Not available" when toggle is OFF
                timeInputs.classList.add('disabled');
                timeInputs.innerHTML = '<span class="not-available">Not available</span>';
            }

            // Update available days counter
            updateAvailableDaysCounter();
        }
    });

    // Function to update the available days counter
    function updateAvailableDaysCounter() {
        const checkedDays = document.querySelectorAll('.day-checkbox:checked').length;
        const availableDaysElement = document.getElementById('available-days-count');
        
        if (availableDaysElement) {
            availableDaysElement.textContent = checkedDays;
        }
    }

    // Legacy notification badge update function (for backward compatibility)
    function updateNotificationBadge() {
        const unreadCount = document.querySelectorAll('.notification-item.unread').length;
        const badge = document.querySelector('.notification-badge');
        
        if (unreadCount === 0 && badge) {
            badge.remove();
        } else if (badge) {
            badge.textContent = unreadCount;
        }
    }
});
