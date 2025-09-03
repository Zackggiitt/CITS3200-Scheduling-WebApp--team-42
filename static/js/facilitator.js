// Navigation between dashboard, calendar, and notifications
document.addEventListener('DOMContentLoaded', function() {
    const dashboardSections = document.querySelectorAll('#welcome, #alert, #stats, #details');
    const calendarView = document.getElementById('calendar-view');
    const notificationsView = document.getElementById('notifications-view');
    const availabilityView = document.getElementById('availability-view');
    const navItems = document.querySelectorAll('.dashboard-nav-item');
    
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
                notificationsView.style.display = 'none';
            } else if (href === '#schedule') {
                // Show calendar view
                dashboardSections.forEach(section => section.style.display = 'none');
                availabilityView.style.display = 'none';
                calendarView.style.display = 'block';
                notificationsView.style.display = 'none';
                initCalendar();
            } else if (href === '#notifications') {
                // Show notifications view
                dashboardSections.forEach(section => section.style.display = 'none');
                availabilityView.style.display = 'none';
                calendarView.style.display = 'none';
                notificationsView.style.display = 'block';
            } else {
                // Show dashboard view
                dashboardSections.forEach(section => section.style.display = 'block');
                availabilityView.style.display = 'none';
                calendarView.style.display = 'none';
                notificationsView.style.display = 'none';
            }
        });
    });

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

    // NOTIFICATIONS FUNCTIONALITY
    // Notification filters
    const filterBtns = document.querySelectorAll('.filter-btn');
    const notificationItems = document.querySelectorAll('.notification-item');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active filter
            filterBtns.forEach(f => f.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            
            // Filter notifications
            notificationItems.forEach(item => {
                if (filter === 'all' || item.getAttribute('data-type') === filter) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    // Mark all as read
    const markAllReadBtn = document.getElementById('mark-all-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            const unreadItems = document.querySelectorAll('.notification-item.unread');
            unreadItems.forEach(item => {
                item.classList.remove('unread');
            });
            
            // Remove notification badge completely
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                badge.remove();
            }
        });
    }

    // Clear all notifications
    const clearAllBtn = document.getElementById('clear-all');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear all notifications?')) {
                const notificationsList = document.getElementById('notifications-list');
                const emptyState = document.getElementById('notifications-empty');
                
                if (notificationsList) notificationsList.style.display = 'none';
                if (emptyState) emptyState.style.display = 'block';
                
                // Update notification badge
                const badge = document.querySelector('.notification-badge');
                if (badge) {
                    badge.remove();
                }
            }
        });
    }
        
    // Function to check if there are any unread notifications and update badge
    function updateNotificationBadge() {
        const unreadCount = document.querySelectorAll('.notification-item.unread').length;
        const badge = document.querySelector('.notification-badge');
        
        if (unreadCount === 0 && badge) {
            badge.remove();
        } else if (badge) {
            badge.textContent = unreadCount;
        }
    }

    // GLOBAL CLICK HANDLER - Only one for all click events
    document.addEventListener('click', function(e) {
        // Handle notification accept/decline buttons
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
            notificationsView.style.display = 'none';
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
});
