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
        // Handle session action buttons (more specific selector)
        if (e.target.closest('.session-item .action-btn.accept')) {
            const sessionItem = e.target.closest('.session-item');
            const statusBadge = sessionItem.querySelector('.tag');
            statusBadge.textContent = 'approved';
            statusBadge.className = 'tag approved';
            
            // Remove action buttons
            const actionsDiv = sessionItem.querySelector('.session-actions');
            if (actionsDiv) {
                actionsDiv.remove();
            }
            
            alert('Session accepted successfully!');
        } else if (e.target.closest('.session-item .action-btn.decline')) {
            const sessionItem = e.target.closest('.session-item');
            sessionItem.style.opacity = '0.5';
            sessionItem.style.textDecoration = 'line-through';
            
            // Remove action buttons
            const actionsDiv = sessionItem.querySelector('.session-actions');
            if (actionsDiv) {
                actionsDiv.remove();
            }
            
            alert('Session declined.');
        }
        
        // Handle notification accept/decline buttons (legacy support)
        else if (e.target.closest('.notification-item .action-btn.accept')) {
            const notification = e.target.closest('.notification-item');
            notification.classList.remove('unread');
            updateNotificationBadge();
            alert('Shift accepted successfully!');
        } else if (e.target.closest('.notification-item .action-btn.decline')) {
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

    // ... existing code ...

    // Unit Selector Functionality
    // Sample unit data with more detailed information
    const units = {
        1: {
            code: 'CITS1001',
            name: 'Introduction to Computing',
            semester: 'Semester 2, 2025',
            status: 'active',
            sessions: 6,
            dateRange: '2/24/2025 - 6/13/2025',
            kpis: {
                thisWeekHours: 4,
                remainingHours: 12,
                totalHours: 16,
                activeSessions: 2
            },
                         upcomingSessions: [
                 { day: 'Monday, Sep 1', date: '01/09/2025', time: '9:00 AM - 11:00 AM', location: 'Stats Lab', topic: 'Statistics Review', status: 'approved' },
                 { day: 'Today (Sep 5)', date: '05/09/2025', time: '10:00 AM - 12:00 PM', location: 'Stats Lab', topic: 'R Programming', status: 'approved' },
                 { day: 'Friday, Sep 12', date: '12/09/2025', time: '10:00 AM - 12:00 PM', location: 'Stats Lab', topic: 'R Programming', status: 'pending' },
                 { day: 'Monday, Sep 8', date: '08/09/2025', time: '2:00 PM - 4:00 PM', location: 'Computer Lab', topic: 'Data Visualization', status: 'approved' }
             ]
        },
        2: {
            code: 'CITS1401',
            name: 'Computer Science',
            semester: 'Semester 1, 2025',
            status: 'active',
            sessions: 4,
            dateRange: '1/15/2025 - 5/30/2025',
            kpis: {
                thisWeekHours: 6,
                remainingHours: 8,
                totalHours: 14,
                activeSessions: 3
            },
            upcomingSessions: [
                { day: 'Wednesday, Sep 3', date: '03/09/2025', time: '1:00 PM - 3:00 PM', location: 'CS Lab', topic: 'Algorithms', status: 'approved' },
                { day: 'Friday, Sep 6', date: '06/09/2025', time: '11:00 AM - 1:00 PM', location: 'CS Lab', topic: 'Data Structures', status: 'approved' }
            ]
        },
        3: {
            code: 'CITS2000',
            name: 'Data Structures',
            semester: 'Semester 2, 2025',
            status: 'active',
            sessions: 8,
            dateRange: '2/24/2025 - 6/13/2025',
            kpis: {
                thisWeekHours: 8,
                remainingHours: 16,
                totalHours: 24,
                activeSessions: 4
            },
            upcomingSessions: [
                { day: 'Tuesday, Sep 2', date: '02/09/2025', time: '9:00 AM - 11:00 AM', location: 'DS Lab', topic: 'Linked Lists', status: 'approved' },
                { day: 'Thursday, Sep 4', date: '04/09/2025', time: '2:00 PM - 4:00 PM', location: 'DS Lab', topic: 'Trees', status: 'approved' },
                { day: 'Monday, Sep 8', date: '08/09/2025', time: '10:00 AM - 12:00 PM', location: 'DS Lab', topic: 'Graphs', status: 'approved' }
            ]
        },
        4: {
            code: 'CITS2200',
            name: 'Algorithms',
            semester: 'Semester 1, 2025',
            status: 'completed',
            sessions: 5,
            dateRange: '1/15/2025 - 5/30/2025',
            kpis: {
                totalHours: 20,
                totalSessions: 5
            },
            pastSessions: [
                { day: 'Monday, Jul 7', date: '07/07/2025', time: '10:00 AM - 12:00 PM', location: 'Algo Lab', topic: 'Sorting Algorithms', status: 'completed' },
                { day: 'Wednesday, Jul 9', date: '09/07/2025', time: '2:00 PM - 4:00 PM', location: 'Algo Lab', topic: 'Search Algorithms', status: 'completed' },
                { day: 'Friday, Jul 11', date: '11/07/2025', time: '9:00 AM - 11:00 AM', location: 'Algo Lab', topic: 'Dynamic Programming', status: 'completed' }
            ]
        },
        5: {
            code: 'CITS3000',
            name: 'Software Engineering',
            semester: 'Semester 2, 2024',
            status: 'completed',
            sessions: 7,
            dateRange: '2/26/2024 - 6/14/2024',
            kpis: {
                totalHours: 28,
                totalSessions: 7
            },
            pastSessions: [
                { day: 'Monday, Jul 7', date: '07/07/2024', time: '10:00 AM - 12:00 PM', location: 'SE Lab', topic: 'Design Patterns', status: 'completed' },
                { day: 'Wednesday, Jul 9', date: '09/07/2024', time: '2:00 PM - 4:00 PM', location: 'SE Lab', topic: 'Testing', status: 'completed' }
            ]
        }
    };

    let currentView = 'unit'; // 'unit', 'all'
    let currentUnitId = 1; // Default to first unit

    // DOM elements for unit selector
    const switchUnitBtn = document.getElementById('switch-unit-trigger');
    const dropdownMenu = document.getElementById('unit-dropdown-menu');
    const allUnitsBtn = document.querySelector('.all-units-btn');
    
    // Update the DOM element selectors to be more specific
    const unitCodeEl = document.querySelector('#unit-selector .unit-code');
    const unitNameEl = document.querySelector('#unit-selector .unit-name');
    const semesterBadgeEl = document.querySelector('#unit-selector .semester-badge');
    const statusBadgeEl = document.querySelector('#unit-selector .status-badge');
    const sessionInfoEl = document.querySelector('#unit-selector .session-info');

    // KPI and Sessions elements
    const statsGrid = document.querySelector('.stats-grid');
    const sessionsSection = document.querySelector('#details .details-card');

    // Initialize unit selector if elements exist
    if (switchUnitBtn && dropdownMenu && allUnitsBtn) {
        initUnitSelector();
    }

    function initUnitSelector() {
        // Toggle dropdown
        switchUnitBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = dropdownMenu.style.display !== 'none';
            
            if (isOpen) {
                closeDropdown();
            } else {
                openDropdown();
            }
        });

        // Handle unit selection
        document.querySelectorAll('.unit-item').forEach(item => {
            item.addEventListener('click', function() {
                const unitId = parseInt(this.dataset.unitId);
                selectUnit(unitId);
                closeDropdown();
            });
        });

        // All Units button
        allUnitsBtn.addEventListener('click', function() {
            showAllUnitsView();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!switchUnitBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                closeDropdown();
            }
        });

        // Initialize with default unit
        selectUnit(currentUnitId);
    }

    function openDropdown() {
        // Calculate position relative to the button
        const buttonRect = switchUnitBtn.getBoundingClientRect();
        const dropdown = dropdownMenu;
        
        // Position dropdown below the button
        dropdown.style.top = (buttonRect.bottom + 4) + 'px';
        dropdown.style.right = (window.innerWidth - buttonRect.right) + 'px';
        
        dropdown.style.display = 'block';
        switchUnitBtn.classList.add('active');
    }

    function closeDropdown() {
        dropdownMenu.style.display = 'none';
        switchUnitBtn.classList.remove('active');
    }

    function selectUnit(unitId) {
        const unit = units[unitId];
        if (!unit) return;

        currentView = 'unit';
        currentUnitId = unitId;
        
        // Update unit display
        unitCodeEl.textContent = unit.code;
        unitNameEl.textContent = unit.name;
        semesterBadgeEl.textContent = unit.semester;
        
        // Update status badge
        statusBadgeEl.className = `status-badge ${unit.status}`;
        if (unit.status === 'active') {
            statusBadgeEl.innerHTML = '<span class="material-icons">check_circle</span>Active';
        } else {
            statusBadgeEl.innerHTML = '<span class="material-icons">check_circle</span>Completed';
        }
        
        // Update session info
        sessionInfoEl.innerHTML = `
            <span class="material-icons">calendar_today</span>
            <span>${unit.sessions} sessions</span>
            <span class="date-range">${unit.dateRange}</span>
        `;

        // Update KPI cards based on unit status
        updateKPICards(unit);
        
        // Update sessions section
        updateSessionsSection(unit);

        // Update active state in dropdown
        document.querySelectorAll('.unit-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-unit-id="${unitId}"]`).classList.add('active');

        console.log(`Switched to unit: ${unit.code} - ${unit.name}`);
    }

    function showAllUnitsView() {
        currentView = 'all';
        
        // Update unit display for all units view
        unitCodeEl.textContent = 'All Units';
        unitNameEl.textContent = 'Overview';
        semesterBadgeEl.textContent = 'Multiple Semesters';
        statusBadgeEl.className = 'status-badge active';
        statusBadgeEl.innerHTML = '<span class="material-icons">check_circle</span>Active';
        
        // Update session info for all units
        const activeUnits = Object.values(units).filter(unit => unit.status === 'active');
        const totalSessions = activeUnits.reduce((sum, unit) => sum + unit.sessions, 0);
        sessionInfoEl.innerHTML = `
            <span class="material-icons">calendar_today</span>
            <span>${totalSessions} sessions</span>
            <span class="date-range">Across all units</span>
        `;

        // Update KPI cards for all units view
        updateAllUnitsKPICards();
        
        // Update sessions section for all units view
        updateAllUnitsSessionsSection();

        console.log('Switched to All Units view');
    }

    function updateKPICards(unit) {
        if (unit.status === 'active') {
            // Active unit KPIs: This Week Hours, Remaining Hours, Total Hours, Active Sessions
            statsGrid.className = 'stats-grid four-cards';
            statsGrid.innerHTML = `
                <div class="stat-card purple">
                    <div class="stat-header">
                        <h4>This Week Hours</h4>
                        <span class="material-icons" aria-hidden="true">schedule</span>
                    </div>
                    <p class="stat-value">${unit.kpis.thisWeekHours}</p>
                    <p class="stat-subtext">2 sessions</p>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header">
                        <h4>Remaining Hours</h4>
                        <span class="material-icons" aria-hidden="true">pending_actions</span>
                    </div>
                    <p class="stat-value">${unit.kpis.remainingHours}</p>
                    <p class="stat-subtext">Total hours - this week hours</p>
                </div>
                <div class="stat-card gray">
                    <div class="stat-header">
                        <h4>Total Hours</h4>
                        <span class="material-icons" aria-hidden="true">calendar_today</span>
                    </div>
                    <p class="stat-value">${unit.kpis.totalHours}</p>
                    <p class="stat-subtext">For this unit</p>
                </div>
                <div class="stat-card green">
                    <div class="stat-header">
                        <h4>Active Sessions</h4>
                        <span class="material-icons" aria-hidden="true">event_available</span>
                    </div>
                    <p class="stat-value">${unit.kpis.activeSessions}</p>
                    <p class="stat-subtext">This week</p>
                </div>
            `;
        } else {
            // Past unit KPIs: Total Hours, Total Sessions
            statsGrid.className = 'stats-grid two-cards';
            statsGrid.innerHTML = `
                <div class="stat-card purple">
                    <div class="stat-header">
                        <h4>Total Hours</h4>
                        <span class="material-icons" aria-hidden="true">schedule</span>
                    </div>
                    <p class="stat-value">${unit.kpis.totalHours}</p>
                    <p class="stat-subtext">For this unit</p>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header">
                        <h4>Total Sessions</h4>
                        <span class="material-icons" aria-hidden="true">calendar_today</span>
                    </div>
                    <p class="stat-value">${unit.kpis.totalSessions}</p>
                    <p class="stat-subtext">Completed</p>
                </div>
            `;
        }
    }

    function updateAllUnitsKPICards() {
        const activeUnits = Object.values(units).filter(unit => unit.status === 'active');
        const totalThisWeekHours = activeUnits.reduce((sum, unit) => sum + unit.kpis.thisWeekHours, 0);
        const totalHours = activeUnits.reduce((sum, unit) => sum + unit.kpis.totalHours, 0);
        const totalActiveSessions = activeUnits.reduce((sum, unit) => sum + unit.kpis.activeSessions, 0);

        statsGrid.className = 'stats-grid three-cards';
        statsGrid.innerHTML = `
            <div class="stat-card purple">
                <div class="stat-header">
                    <h4>This Week Hours</h4>
                    <span class="material-icons" aria-hidden="true">schedule</span>
                </div>
                <p class="stat-value">${totalThisWeekHours}</p>
                <p class="stat-subtext">Across all units</p>
            </div>
            <div class="stat-card blue">
                <div class="stat-header">
                    <h4>Total Hours</h4>
                    <span class="material-icons" aria-hidden="true">calendar_today</span>
                </div>
                <p class="stat-value">${totalHours}</p>
                <p class="stat-subtext">Across all units</p>
            </div>
            <div class="stat-card green">
                <div class="stat-header">
                    <h4>Active Sessions</h4>
                    <span class="material-icons" aria-hidden="true">event_available</span>
                </div>
                <p class="stat-value">${totalActiveSessions}</p>
                <p class="stat-subtext">This week</p>
            </div>
        `;
    }

    function updateSessionsSection(unit) {
        const sessionsTitle = `${unit.code} Sessions`;
        let sessionsHTML = `
            <div class="card-header">
                <h3>${sessionsTitle}</h3>
                <a href="#" class="view-all-link">View All</a>
            </div>
            <div class="session-list">
        `;

        if (unit.status === 'active' && unit.upcomingSessions) {
            // Sort sessions by date and take only top 3
            const sortedSessions = unit.upcomingSessions.sort((a, b) => {
                const dateA = new Date(a.date.split('/').reverse().join('-'));
                const dateB = new Date(b.date.split('/').reverse().join('-'));
                return dateA - dateB;
            });
            
            const top3Sessions = sortedSessions.slice(0, 3);
            const remainingCount = unit.upcomingSessions.length - 3;
            
            top3Sessions.forEach(session => {
                const hasActions = session.status === 'pending';
                sessionsHTML += `
                    <div class="session-item">
                        <div class="session-info">
                            <div class="session-title">
                                <div>
                                    <h4>${session.topic}</h4>
                                    <p class="session-full-date">${session.date}</p>
                                </div>
                                <span class="tag ${session.status}">${session.status}</span>
                            </div>
                            <p class="session-time">${session.time}</p>
                            <p class="session-location">${session.location}</p>
                        </div>
                        ${hasActions ? `
                            <div class="session-actions">
                                <button class="action-btn accept">
                                    <span class="material-icons">check</span>
                                    Accept
                                </button>
                                <button class="action-btn decline">
                                    Decline
                                </button>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            // Add "more sessions" message if there are more than 3
            if (remainingCount > 0) {
                sessionsHTML += `
                    <div class="more-sessions-message">
                        <p>${remainingCount} more session${remainingCount > 1 ? 's' : ''} available. Click "View All" to see all sessions.</p>
                    </div>
                `;
            }
        } else if (unit.status === 'completed' && unit.pastSessions) {
            unit.pastSessions.forEach(session => {
                sessionsHTML += `
                    <div class="session-item">
                        <div class="session-info">
                            <div class="session-title">
                                <div>
                                    <h4>${session.topic}</h4>
                                    <p class="session-full-date">${session.date}</p>
                                </div>
                                <span class="tag confirmed">${session.status}</span>
                            </div>
                            <p class="session-time">${session.time}</p>
                            <p class="session-location">${session.location}</p>
                        </div>
                    </div>
                `;
            });
        }

        sessionsHTML += '</div>';
        sessionsSection.innerHTML = sessionsHTML;
    }

    function updateAllUnitsSessionsSection() {
        const activeUnits = Object.values(units).filter(unit => unit.status === 'active');
        const completedUnits = Object.values(units).filter(unit => unit.status === 'completed');
        
        let sessionsHTML = `
            <div class="card-header">
                <h3>Your Sessions</h3>
                <a href="#" class="view-all-link">View All</a>
            </div>
            <div class="session-list">
        `;

        // Add current & upcoming sessions from active units
        sessionsHTML += `
            <div class="session-group-header">
                <h4>Current & Upcoming Sessions</h4>
                <span class="session-count-badge">${activeUnits.reduce((sum, unit) => sum + (unit.upcomingSessions ? unit.upcomingSessions.length : 0), 0)} sessions</span>
            </div>
        `;

        activeUnits.forEach(unit => {
            if (unit.upcomingSessions) {
                // Sort sessions by date and take only top 2
                const sortedSessions = unit.upcomingSessions.sort((a, b) => {
                    const dateA = new Date(a.date.split('/').reverse().join('-'));
                    const dateB = new Date(b.date.split('/').reverse().join('-'));
                    return dateA - dateB;
                });
                
                const top2Sessions = sortedSessions.slice(0, 2);
                const remainingCount = unit.upcomingSessions.length - 2;
                
                sessionsHTML += `
                    <div class="unit-session-group">
                        <div class="unit-header">
                            <span class="unit-code-small">${unit.code}</span>
                            <span class="unit-session-count">${unit.upcomingSessions.length} sessions</span>
                        </div>
                `;
                
                top2Sessions.forEach(session => {
                    const hasActions = session.status === 'pending';
                    sessionsHTML += `
                        <div class="session-item">
                            <div class="session-info">
                                <div class="session-title">
                                    <div>
                                        <h4>${session.topic}</h4>
                                        <p class="session-full-date">${session.date}</p>
                                    </div>
                                    <span class="tag ${session.status}">${session.status}</span>
                                </div>
                                <p class="session-time">${session.time}</p>
                                <p class="session-location">${session.location}</p>
                            </div>
                            ${hasActions ? `
                                <div class="session-actions">
                                    <button class="action-btn accept">
                                        <span class="material-icons">check</span>
                                        Accept
                                    </button>
                                    <button class="action-btn decline">
                                        Decline
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    `;
                });
                
                // Add "more sessions" message if there are remaining sessions
                if (remainingCount > 0) {
                    sessionsHTML += `
                        <div class="more-sessions-message">
                            +${remainingCount} more session${remainingCount === 1 ? '' : 's'} in ${unit.code}. Click "View All" to see all sessions.
                        </div>
                    `;
                }
                
                sessionsHTML += '</div>';
            }
        });

        // Add past sessions from completed units
        const pastUnits = Object.values(units).filter(unit => unit.status === 'completed');
        if (pastUnits.length > 0) {
            sessionsHTML += `
                <div class="session-group-header">
                    <h4>Past Sessions</h4>
                    <span class="session-count-badge">${pastUnits.reduce((sum, unit) => sum + (unit.pastSessions ? unit.pastSessions.length : 0), 0)} sessions</span>
                </div>
            `;

            pastUnits.forEach(unit => {
                if (unit.pastSessions) {
                    sessionsHTML += `
                        <div class="unit-session-group">
                            <div class="unit-header">
                                <span class="unit-code-small">${unit.code}</span>
                                <span class="unit-session-count">${unit.pastSessions.length} sessions</span>
                            </div>
                    `;
                    
                    unit.pastSessions.forEach(session => {
                        sessionsHTML += `
                            <div class="session-item">
                                <div class="session-info">
                                    <div class="session-title">
                                        <div>
                                            <h4>${session.topic}</h4>
                                            <p class="session-full-date">${session.date}</p>
                                        </div>
                                        <span class="tag completed">${session.status}</span>
                                    </div>
                                    <p class="session-time">${session.time}</p>
                                    <p class="session-location">${session.location}</p>
                                </div>
                            </div>
                        `;
                    });
                    
                    sessionsHTML += '</div>';
                }
            });
        }

        sessionsHTML += '</div>';
        sessionsSection.innerHTML = sessionsHTML;
        
        // Add event listener for "View All" button with a small delay to ensure DOM is updated
        setTimeout(() => {
            const viewAllLink = sessionsSection.querySelector('.view-all-link');
            console.log('Looking for View All link in All Units view:', viewAllLink);
            if (viewAllLink) {
                viewAllLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    console.log('View All clicked for All Units view');
                    showAllUnitsSessionsModal();
                });
                console.log('View All event listener added for All Units view');
            } else {
                console.log('View All link not found for All Units view');
            }
        }, 100);
    }

    // Modal Functions
    function showSessionsModal(unit) {
        console.log('showSessionsModal called for unit:', unit.code);
        const modal = document.getElementById('sessions-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalSubtitle = document.getElementById('modal-subtitle');
        const modalSessionsList = document.getElementById('modal-sessions-list');
        
        console.log('Modal elements found:', {
            modal: !!modal,
            modalTitle: !!modalTitle,
            modalSubtitle: !!modalSubtitle,
            modalSessionsList: !!modalSessionsList
        });
        
        if (!modal) {
            console.error('Modal element not found!');
            return;
        }
        
        // Set modal title
        modalTitle.textContent = `All ${unit.code} Sessions`;
        
        // Set modal subtitle
        const totalSessions = (unit.upcomingSessions ? unit.upcomingSessions.length : 0) + 
                             (unit.pastSessions ? unit.pastSessions.length : 0);
        modalSubtitle.textContent = `View all your sessions for ${unit.code}. You can accept or decline pending session assignments. Showing ${totalSessions} sessions for ${unit.code}`;
        
        // Generate sessions list
        let modalSessionsHTML = '';
        
        // Add upcoming sessions if they exist
        if (unit.upcomingSessions && unit.upcomingSessions.length > 0) {
            const sortedUpcomingSessions = unit.upcomingSessions.sort((a, b) => {
                const dateA = new Date(a.date.split('/').reverse().join('-'));
                const dateB = new Date(b.date.split('/').reverse().join('-'));
                return dateA - dateB;
            });
            
            sortedUpcomingSessions.forEach(session => {
                const hasActions = session.status === 'pending';
                modalSessionsHTML += `
                    <div class="session-item">
                        <div class="session-info">
                            <div class="session-title">
                                <div>
                                    <h4>${session.topic}</h4>
                                    <p class="session-full-date">${session.date}</p>
                                </div>
                                <span class="tag ${session.status}">${session.status}</span>
                            </div>
                            <p class="session-time">${session.time}</p>
                            <p class="session-location">${session.location}</p>
                        </div>
                        ${hasActions ? `
                            <div class="session-actions">
                                <button class="action-btn accept">
                                    <span class="material-icons">check</span>
                                    Accept
                                </button>
                                <button class="action-btn decline">
                                    Decline
                                </button>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
        }
        
        // Add past sessions if they exist
        if (unit.pastSessions && unit.pastSessions.length > 0) {
            const sortedPastSessions = unit.pastSessions.sort((a, b) => {
                const dateA = new Date(a.date.split('/').reverse().join('-'));
                const dateB = new Date(b.date.split('/').reverse().join('-'));
                return dateB - dateA; // Reverse order for past sessions (most recent first)
            });
            
            sortedPastSessions.forEach(session => {
                modalSessionsHTML += `
                    <div class="session-item">
                        <div class="session-info">
                            <div class="session-title">
                                <div>
                                    <h4>${session.topic}</h4>
                                    <p class="session-full-date">${session.date}</p>
                                </div>
                                <span class="tag completed">${session.status}</span>
                            </div>
                            <p class="session-time">${session.time}</p>
                            <p class="session-location">${session.location}</p>
                        </div>
                    </div>
                `;
            });
        }
        
        modalSessionsList.innerHTML = modalSessionsHTML;
        
        // Show modal
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function hideSessionsModal() {
        const modal = document.getElementById('sessions-modal');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }

    function showAllUnitsSessionsModal() {
        console.log('showAllUnitsSessionsModal called');
        const modal = document.getElementById('sessions-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalSubtitle = document.getElementById('modal-subtitle');
        const modalSessionsList = document.getElementById('modal-sessions-list');
        
        console.log('Modal elements found for All Units:', {
            modal: !!modal,
            modalTitle: !!modalTitle,
            modalSubtitle: !!modalSubtitle,
            modalSessionsList: !!modalSessionsList
        });
        
        if (!modal) {
            console.error('Modal element not found!');
            return;
        }

        // Set modal title and subtitle
        modalTitle.textContent = 'All Your Sessions';
        modalSubtitle.textContent = 'View all your sessions across all units organized by status and unit. You can accept or decline pending session assignments.';

        // Get all units data
        const activeUnits = Object.values(units).filter(unit => unit.status === 'active');
        const completedUnits = Object.values(units).filter(unit => unit.status === 'completed');
        
        let modalHTML = '';

        // Add current & upcoming sessions from active units
        if (activeUnits.length > 0) {
            modalHTML += `
                <div class="modal-session-group">
                    <div class="modal-group-header">
                        <h4>Current & Upcoming Sessions</h4>
                        <span class="modal-session-count">${activeUnits.reduce((sum, unit) => sum + (unit.upcomingSessions ? unit.upcomingSessions.length : 0), 0)} sessions</span>
                    </div>
            `;

            activeUnits.forEach(unit => {
                if (unit.upcomingSessions && unit.upcomingSessions.length > 0) {
                    modalHTML += `
                        <div class="modal-unit-group">
                            <div class="modal-unit-header">
                                <span class="modal-unit-code">${unit.code}</span>
                                <span class="modal-unit-session-count">${unit.upcomingSessions.length} sessions</span>
                            </div>
                    `;
                    
                    // Sort sessions by date
                    const sortedSessions = unit.upcomingSessions.sort((a, b) => {
                        const dateA = new Date(a.date.split('/').reverse().join('-'));
                        const dateB = new Date(b.date.split('/').reverse().join('-'));
                        return dateA - dateB;
                    });
                    
                    sortedSessions.forEach(session => {
                        const hasActions = session.status === 'pending';
                        modalHTML += `
                            <div class="modal-session-item">
                                <div class="modal-session-info">
                                    <div class="modal-session-title">
                                        <div>
                                            <h4>${session.topic}</h4>
                                            <p class="modal-session-date">${session.date}</p>
                                        </div>
                                        <span class="modal-tag ${session.status}">${session.status}</span>
                                    </div>
                                    <p class="modal-session-time">${session.time}</p>
                                    <p class="modal-session-location">${session.location}</p>
                                </div>
                                ${hasActions ? `
                                    <div class="modal-session-actions">
                                        <button class="modal-action-btn accept">
                                            <span class="material-icons">check</span>
                                            Accept
                                        </button>
                                        <button class="modal-action-btn decline">
                                            Decline
                                        </button>
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    });
                    
                    modalHTML += '</div>';
                }
            });
            
            modalHTML += '</div>';
        }

        // Add past sessions from completed units
        if (completedUnits.length > 0) {
            modalHTML += `
                <div class="modal-session-group">
                    <div class="modal-group-header">
                        <h4>Past Sessions</h4>
                        <span class="modal-session-count">${completedUnits.reduce((sum, unit) => sum + (unit.pastSessions ? unit.pastSessions.length : 0), 0)} sessions</span>
                    </div>
            `;

            completedUnits.forEach(unit => {
                if (unit.pastSessions && unit.pastSessions.length > 0) {
                    modalHTML += `
                        <div class="modal-unit-group">
                            <div class="modal-unit-header">
                                <span class="modal-unit-code">${unit.code}</span>
                                <span class="modal-unit-session-count">${unit.pastSessions.length} sessions</span>
                            </div>
                    `;
                    
                    // Sort sessions by date (most recent first)
                    const sortedSessions = unit.pastSessions.sort((a, b) => {
                        const dateA = new Date(a.date.split('/').reverse().join('-'));
                        const dateB = new Date(b.date.split('/').reverse().join('-'));
                        return dateB - dateA;
                    });
                    
                    sortedSessions.forEach(session => {
                        modalHTML += `
                            <div class="modal-session-item">
                                <div class="modal-session-info">
                                    <div class="modal-session-title">
                                        <div>
                                            <h4>${session.topic}</h4>
                                            <p class="modal-session-date">${session.date}</p>
                                        </div>
                                        <span class="modal-tag completed">${session.status}</span>
                                    </div>
                                    <p class="modal-session-time">${session.time}</p>
                                    <p class="modal-session-location">${session.location}</p>
                                </div>
                            </div>
                        `;
                    });
                    
                    modalHTML += '</div>';
                }
            });
            
            modalHTML += '</div>';
        }

        modalSessionsList.innerHTML = modalHTML;
        modal.style.display = 'flex';
        
        console.log('All Units modal displayed');
    }

    // Initialize modal event listeners
    function initModalListeners() {
        console.log('Initializing modal listeners...');
        const modal = document.getElementById('sessions-modal');
        const closeBtn = document.getElementById('modal-close-btn');
        
        console.log('Modal elements for listeners:', {
            modal: !!modal,
            closeBtn: !!closeBtn
        });
        
        if (closeBtn) {
            closeBtn.addEventListener('click', hideSessionsModal);
            console.log('Close button listener added');
        }
        
        // Close modal when clicking outside
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    hideSessionsModal();
                }
            });
            console.log('Modal overlay listener added');
        }
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
                hideSessionsModal();
            }
        });
        console.log('Escape key listener added');
    }

    // Initialize modal listeners when DOM is loaded
    initModalListeners();
    
    // Add event delegation for "View All" buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.view-all-link')) {
            e.preventDefault();
            console.log('View All clicked via event delegation');
            
            // Find the sessions section
            const sessionsSection = e.target.closest('#details .details-card');
            if (sessionsSection) {
                // Check if this is the "View All Units" view
                if (currentView === 'all') {
                    console.log('Opening modal for All Units view');
                    showAllUnitsSessionsModal();
                } else if (currentView === 'unit' && currentUnitId) {
                    // Get the unit from the current view
                    const unit = units[currentUnitId];
                    if (unit) {
                        console.log('Opening modal for unit:', unit.code);
                        showSessionsModal(unit);
                    }
                }
            }
        }
    });
});
