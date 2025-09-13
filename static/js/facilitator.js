// Navigation between dashboard, calendar, and notifications
document.addEventListener('DOMContentLoaded', function() {
    const dashboardSections = document.querySelectorAll('#welcome, #alert, #stats, #details');
    const calendarView = document.getElementById('calendar-view');
    const unavailabilityView = document.getElementById('unavailability-view');
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

            if (href === '#unavailability') {
                // Show unavailability view
                dashboardSections.forEach(section => section.style.display = 'none');
                unavailabilityView.style.display = 'block';
                calendarView.style.display = 'none';
                document.body.classList.remove('calendar-view-active');
                // Hide unavailability alert in unavailability view
                const unavailabilityAlert = document.getElementById('unavailability-alert');
                if (unavailabilityAlert) unavailabilityAlert.style.display = 'none';
                // Initialize unavailability functionality
                initUnavailabilityView();
            } else if (href === '#schedule') {
                // Show calendar view
                dashboardSections.forEach(section => section.style.display = 'none');
                unavailabilityView.style.display = 'none';
                calendarView.style.display = 'block';
                document.body.classList.add('calendar-view-active');
                initCalendar();
                // Hide unavailability alert in schedule view
                const unavailabilityAlert = document.getElementById('unavailability-alert');
                if (unavailabilityAlert) unavailabilityAlert.style.display = 'none';
            } else {
                // Show dashboard view
                dashboardSections.forEach(section => section.style.display = 'block');
                unavailabilityView.style.display = 'none';
                calendarView.style.display = 'none';
                document.body.classList.remove('calendar-view-active');
                // Show unavailability alert in dashboard view
                const unavailabilityAlert = document.getElementById('unavailability-alert');
                if (unavailabilityAlert) unavailabilityAlert.style.display = 'block';
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
        loadUnavailabilityDataForCalendar();
        generateCalendarDays();
    }
    
    // Function to load unavailability data for the calendar
    function loadUnavailabilityDataForCalendar() {
        // Get current unit ID
        const currentUnitId = window.currentUnitId;
        
        if (currentUnitId) {
            fetch(`/facilitator/unavailability?unit_id=${currentUnitId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error loading unavailability for calendar:', data.error);
                        window.unavailabilityData = [];
                        return;
                    }
                    
                    window.unavailabilityData = data.unavailabilities || [];
                    console.log('Loaded unavailability data for calendar:', window.unavailabilityData);
                })
                .catch(error => {
                    console.error('Error loading unavailability data for calendar:', error);
                    window.unavailabilityData = [];
                });
        } else {
            window.unavailabilityData = [];
        }
    }
    
    // Function to show all sessions for a specific date
    function showAllSessionsForDate(formattedDate, eventsData = null) {
        // If eventsData is not provided, collect all events for this date
        if (!eventsData) {
            const allEvents = [];
            
            if (window.unitsData) {
                window.unitsData.forEach(unit => {
                    // Check upcoming sessions
                    if (unit.upcoming_sessions) {
                        unit.upcoming_sessions.forEach(session => {
                            if (session.date === formattedDate) {
                                const statusClass = session.status === 'confirmed' ? 'confirmed' : 'pending';
                                const eventText = `${unit.code}\n${session.topic}\n${session.time}\n${session.location}`;
                                allEvents.push({
                                    text: eventText,
                                    class: statusClass,
                                    session: session,
                                    unit: unit
                                });
                            }
                        });
                    }
                    
                    // Check past sessions
                    if (unit.past_sessions) {
                        unit.past_sessions.forEach(session => {
                            if (session.date === formattedDate) {
                                const eventText = `${unit.code}\n${session.topic}\n${session.time}\n${session.location}`;
                                allEvents.push({
                                    text: eventText,
                                    class: 'past',
                                    session: session,
                                    unit: unit
                                });
                            }
                        });
                    }
                });
            }
            
            // Sort events by time
            allEvents.sort((a, b) => {
                const timeA = a.session.time.split(' - ')[0];
                const timeB = b.session.time.split(' - ')[0];
                return timeA.localeCompare(timeB);
            });
            
            eventsData = allEvents;
        }
        
        // Show modal with all sessions
        showDateSessionsModal(formattedDate, eventsData);
    }
    
    // Function to show date sessions modal
    function showDateSessionsModal(date, sessions) {
        const modal = document.getElementById('date-sessions-modal');
        const modalTitle = document.getElementById('date-modal-title');
        const modalSubtitle = document.getElementById('date-modal-subtitle');
        const modalSessionsList = document.getElementById('date-modal-sessions-list');
        
        // Format date for display (convert dd/mm/yyyy to readable format)
        const [day, month, year] = date.split('/');
        const displayDate = new Date(year, month - 1, day);
        const formattedDisplayDate = displayDate.toLocaleDateString('en-AU', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        modalTitle.textContent = `Sessions for ${formattedDisplayDate}`;
        modalSubtitle.textContent = `${sessions.length} session${sessions.length !== 1 ? 's' : ''} scheduled`;
        
        // Generate session list HTML
        const sessionsHTML = sessions.map(session => `
            <div class="modal-session-item ${session.class}">
                <div class="session-info">
                    <div class="session-text">${session.text}</div>
                </div>
            </div>
        `).join('');
        
        modalSessionsList.innerHTML = sessionsHTML;
        
        // Show modal
        modal.style.display = 'flex';
        
        // Ensure close button has event listener (fallback)
        const closeBtn = document.getElementById('date-modal-close-btn');
        if (closeBtn) {
            closeBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Date modal close button clicked (fallback)');
                closeDateSessionsModal();
            };
        }
    }
    
    // Function to close date sessions modal
    function closeDateSessionsModal() {
        console.log('closeDateSessionsModal called');
        const modal = document.getElementById('date-sessions-modal');
        if (modal) {
            modal.style.display = 'none';
            console.log('Date modal closed');
        } else {
            console.error('Date modal element not found!');
        }
    }
    
    // Function to check if a date is unavailable
    function isDateUnavailable(formattedDate) {
        // Check if we have unavailability data
        if (window.unavailabilityData && Array.isArray(window.unavailabilityData)) {
            return window.unavailabilityData.some(unav => {
                // Convert unavailability date to match our format
                const unavDate = new Date(unav.date);
                const unavFormatted = String(unavDate.getDate()).padStart(2, '0') + '/' + 
                                    String(unavDate.getMonth() + 1).padStart(2, '0') + '/' + 
                                    String(unavDate.getFullYear());
                return unavFormatted === formattedDate;
            });
        }
        return false;
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
        
        // Fix: Calculate previous month days correctly
        for (let i = startingDayOfWeek; i > 0; i--) {
            const dayNumber = daysInPrevMonth - i + 1;
            const dayElement = createDayElement(dayNumber, true);
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
    
    // Function to refresh calendar when unit data changes
    function refreshCalendar() {
        if (document.getElementById('calendar-view') && document.getElementById('calendar-view').style.display === 'block') {
            loadUnavailabilityDataForCalendar();
            // Small delay to ensure unavailability data is loaded before generating calendar
            setTimeout(() => {
                generateCalendarDays();
            }, 100);
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
        
        // Check availability for this date
        if (!isOtherMonth) {
            const formattedDate = String(dayNumber).padStart(2, '0') + '/' + 
                                 String(month + 1).padStart(2, '0') + '/' + 
                                 String(year);
            
            // Check if date is unavailable
            if (isDateUnavailable(formattedDate)) {
                dayElement.classList.add('unavailable');
            } else {
                // Check if there are active units (for availability indication)
                const hasActiveUnits = window.unitsData && window.unitsData.some(unit => unit.status === 'active');
                if (hasActiveUnits) {
                    dayElement.classList.add('available');
                }
            }
        }
        
        dayElement.innerHTML = `
            <div class="day-number">${dayNumber}</div>
            <div class="day-events">
                ${generateEvents(dayNumber, isOtherMonth)}
            </div>
        `;
        
        // Add click handler for date cell
        if (!isOtherMonth) {
            dayElement.style.cursor = 'pointer';
            dayElement.addEventListener('click', function() {
                const formattedDate = String(dayNumber).padStart(2, '0') + '/' + 
                                     String(currentDate.getMonth() + 1).padStart(2, '0') + '/' + 
                                     String(currentDate.getFullYear());
                showAllSessionsForDate(formattedDate);
            });
        }
        
        return dayElement;
    }
    
    function generateEvents(dayNumber, isOtherMonth) {
        if (isOtherMonth) return '';
        
        const allEvents = [];
        
        // Get current calendar date
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const currentDateObj = new Date(year, month, dayNumber);
        
        // Format date to match session date format (dd/mm/yyyy)
        const formattedDate = String(dayNumber).padStart(2, '0') + '/' + 
                             String(month + 1).padStart(2, '0') + '/' + 
                             String(year);
        
        // Get sessions for this date from all units
        if (window.unitsData) {
            window.unitsData.forEach(unit => {
                // Check upcoming sessions
                if (unit.upcoming_sessions) {
                    unit.upcoming_sessions.forEach(session => {
                        if (session.date === formattedDate) {
                            const statusClass = session.status === 'confirmed' ? 'confirmed' : 'pending';
                            const eventText = `${unit.code}\n${session.topic}\n${session.time}\n${session.location}`;
                            allEvents.push({
                                text: eventText,
                                class: statusClass,
                                session: session,
                                unit: unit
                            });
                        }
                    });
                }
                
                // Check past sessions (for historical view)
                if (unit.past_sessions) {
                    unit.past_sessions.forEach(session => {
                        if (session.date === formattedDate) {
                            const eventText = `${unit.code}\n${session.topic}\n${session.time}\n${session.location}`;
                            allEvents.push({
                                text: eventText,
                                class: 'past',
                                session: session,
                                unit: unit
                            });
                        }
                    });
                }
            });
        }
        
        // Sort events by time (earliest first)
        allEvents.sort((a, b) => {
            const timeA = a.session.time.split(' - ')[0];
            const timeB = b.session.time.split(' - ')[0];
            return timeA.localeCompare(timeB);
        });
        
        // Show only top 2 sessions
        const displayEvents = allEvents.slice(0, 2);
        const remainingCount = allEvents.length - 2;
        
        let result = displayEvents.map(event => 
            `<div class="event ${event.class}" title="${event.text}">${event.text}</div>`
        ).join('');
        
        // Add overflow message if there are more sessions
        if (remainingCount > 0) {
            result += `<div class="overflow-message" onclick="showAllSessionsForDate('${formattedDate}', ${JSON.stringify(allEvents).replace(/"/g, '&quot;')})">${remainingCount} more sessions. Click date to see more</div>`;
        }
        
        return result;
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
            
            // Add active state to unavailability tab
            const unavailabilityNavItem = document.querySelector('a[href="#unavailability"]');
            if (unavailabilityNavItem) {
                unavailabilityNavItem.classList.add('active');
            }
            
            // Hide all sections and show unavailability
            dashboardSections.forEach(section => section.style.display = 'none');
            unavailabilityView.style.display = 'block';
            calendarView.style.display = 'none';
            // Hide unavailability alert in unavailability view
            const unavailabilityAlert = document.getElementById('unavailability-alert');
            if (unavailabilityAlert) unavailabilityAlert.style.display = 'none';
            
            // Initialize unavailability functionality
            initUnavailabilityView();
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
    // Use dynamic data from backend instead of hardcoded values
    const units = {};
    
    // Convert backend data to the format expected by the frontend
    if (window.unitsData) {
        window.unitsData.forEach(unitData => {
            units[unitData.id] = {
                id: unitData.id,
                code: unitData.code,
                name: unitData.name,
                semester: unitData.semester,
                status: unitData.status,
                sessions: unitData.sessions,
                dateRange: unitData.date_range,
                start_date: unitData.start_date,
                end_date: unitData.end_date,
                kpis: {
                    thisWeekHours: unitData.kpis.this_week_hours,
                    remainingHours: unitData.kpis.remaining_hours,
                    totalHours: unitData.kpis.total_hours,
                    activeSessions: unitData.kpis.active_sessions,
                    totalSessions: unitData.kpis.total_sessions
                },
                upcomingSessions: unitData.upcoming_sessions || [],
                pastSessions: unitData.past_sessions || []
            };
        });
    }

    let currentView = 'unit'; // 'unit', 'all'
    let currentUnitId = window.currentUnitId || null; // Use current unit from backend

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

        // Initialize with current unit or first available unit
        if (currentUnitId && units[currentUnitId]) {
            selectUnit(currentUnitId);
        } else if (Object.keys(units).length > 0) {
            // Use first available unit if no current unit
            const firstUnitId = Object.keys(units)[0];
            selectUnit(firstUnitId);
        }
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
        if (!unit) {
            console.warn(`Unit with ID ${unitId} not found`);
            return;
        }

        currentView = 'unit';
        currentUnitId = unitId;
        
        // Show navigation tabs and unavailability alert for individual unit views
        showElementsForUnitView();
        
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

        // Update unavailability view if it's currently visible
        updateUnavailabilityViewForUnit(unit);

        // Refresh calendar if it's currently visible
        refreshCalendar();

        // Update active state in dropdown
        document.querySelectorAll('.unit-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-unit-id="${unitId}"]`).classList.add('active');

        console.log(`Switched to unit: ${unit.code} - ${unit.name}`);
    }

    function showAllUnitsView() {
        currentView = 'all';
        
        // Hide navigation tabs and unavailability alert for "View All Units"
        hideElementsForAllUnitsView();
        
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

        // Refresh calendar if it's currently visible
        refreshCalendar();

        console.log('Switched to All Units view');
    }

    function hideElementsForAllUnitsView() {
        // Hide navigation tabs
        const dashboardNav = document.getElementById('dashboard-nav');
        const unavailabilityNav = document.getElementById('unavailability-nav');
        const scheduleNav = document.getElementById('schedule-nav');
        
        // Hide unavailability alert
        const unavailabilityAlert = document.getElementById('unavailability-alert');
        
        if (dashboardNav) dashboardNav.style.display = 'none';
        if (unavailabilityNav) unavailabilityNav.style.display = 'none';
        if (scheduleNav) scheduleNav.style.display = 'none';
        if (unavailabilityAlert) unavailabilityAlert.style.display = 'none';
    }

    function showElementsForUnitView() {
        // Show navigation tabs
        const dashboardNav = document.getElementById('dashboard-nav');
        const unavailabilityNav = document.getElementById('unavailability-nav');
        const scheduleNav = document.getElementById('schedule-nav');
        
        // Show unavailability alert only if we're on the dashboard tab
        const unavailabilityAlert = document.getElementById('unavailability-alert');
        const unavailabilityView = document.getElementById('unavailability-view');
        
        if (dashboardNav) dashboardNav.style.display = 'flex';
        if (unavailabilityNav) unavailabilityNav.style.display = 'flex';
        if (scheduleNav) scheduleNav.style.display = 'flex';
        
        // Only show alert if we're on dashboard tab (unavailability view is hidden)
        if (unavailabilityAlert) {
            if (unavailabilityView && unavailabilityView.style.display === 'block') {
                // We're on unavailability tab, hide the alert
                unavailabilityAlert.style.display = 'none';
            } else {
                // We're on dashboard tab, show the alert
                unavailabilityAlert.style.display = 'block';
            }
        }
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
                    <p class="stat-subtext">${unit.kpis.activeSessions} sessions this week</p>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header">
                        <h4>Remaining Hours</h4>
                        <span class="material-icons" aria-hidden="true">pending_actions</span>
                    </div>
                    <p class="stat-value">${unit.kpis.remainingHours || 0}</p>
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

        // Show sessions based on unit status
        if (unit.status === 'active') {
            // For active units: show upcoming sessions
            if (unit.upcomingSessions && unit.upcomingSessions.length > 0) {
                // Sort upcoming sessions by date
                const sortedUpcomingSessions = unit.upcomingSessions.sort((a, b) => {
                    const dateA = new Date(a.date.split('/').reverse().join('-'));
                    const dateB = new Date(b.date.split('/').reverse().join('-'));
                    return dateA - dateB;
                });
                
                // Show only top 5 upcoming sessions
                const top5Sessions = sortedUpcomingSessions.slice(0, 5);
                const remainingCount = sortedUpcomingSessions.length - 5;
                
                top5Sessions.forEach(session => {
                    const hasActions = session.status === 'pending';
                    const statusClass = session.status === 'confirmed' ? 'confirmed' : 'pending';
                    const statusText = session.status === 'confirmed' ? 'Confirmed' : 'Pending';
                    
                    sessionsHTML += `
                        <div class="session-item">
                            <div class="session-info">
                                <div class="session-title">
                                    <div>
                                        <h4>${session.topic}</h4>
                                        <p class="session-full-date">${session.date}</p>
                                    </div>
                                    <span class="tag ${statusClass}">${statusText}</span>
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
                
                // Add "more sessions" message if there are more than 5 upcoming sessions
                if (remainingCount > 0) {
                    sessionsHTML += `
                        <div class="more-sessions-message">
                            <p>+${remainingCount} more session${remainingCount > 1 ? 's' : ''} in ${unit.code}. Click "View All" to see all sessions.</p>
                        </div>
                    `;
                }
                
                // Also check if there are completed sessions for active units
                if (unit.pastSessions && unit.pastSessions.length > 0) {
                    sessionsHTML += `
                        <div class="more-sessions-message">
                            <p>+${unit.pastSessions.length} more session${unit.pastSessions.length > 1 ? 's' : ''} that are completed in ${unit.code}. Click "View All" to see all sessions.</p>
                        </div>
                    `;
                }
            } else {
                // No upcoming sessions for active unit
                sessionsHTML += `
                    <div class="no-sessions-message">
                        <p>No upcoming sessions for ${unit.code}.</p>
                    </div>
                `;
            }
        } else if (unit.status === 'completed') {
            // For past units: show past sessions
            if (unit.pastSessions && unit.pastSessions.length > 0) {
                // Sort past sessions by date (most recent first)
                const sortedPastSessions = unit.pastSessions.sort((a, b) => {
                    const dateA = new Date(a.date.split('/').reverse().join('-'));
                    const dateB = new Date(b.date.split('/').reverse().join('-'));
                    return dateB - dateA; // Reverse order for most recent first
                });
                
                // Show only top 5 most recent past sessions
                const top5Sessions = sortedPastSessions.slice(0, 5);
                const remainingCount = sortedPastSessions.length - 5;
                
                top5Sessions.forEach(session => {
                    sessionsHTML += `
                        <div class="session-item">
                            <div class="session-info">
                                <div class="session-title">
                                    <div>
                                        <h4>${session.topic}</h4>
                                        <p class="session-full-date">${session.date}</p>
                                    </div>
                                    <span class="tag completed">Completed</span>
                                </div>
                                <p class="session-time">${session.time}</p>
                                <p class="session-location">${session.location}</p>
                            </div>
                        </div>
                    `;
                });
                
                // Add "more sessions" message if there are more than 5 past sessions
                if (remainingCount > 0) {
                    sessionsHTML += `
                        <div class="more-sessions-message">
                            <p>+${remainingCount} more session${remainingCount > 1 ? 's' : ''} in ${unit.code}. Click "View All" to see all sessions.</p>
                        </div>
                    `;
                }
            } else {
                // No past sessions for completed unit
                sessionsHTML += `
                    <div class="no-sessions-message">
                        <p>No sessions found for ${unit.code}.</p>
                    </div>
                `;
            }
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
            <div class="session-group-header upcoming-sessions-header">
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
                <div class="session-group-header past-sessions-header">
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
                    <div class="modal-group-header upcoming-sessions-header">
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
                    <div class="modal-group-header past-sessions-header">
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
        
        // Add event listeners for date sessions modal
        const dateModal = document.getElementById('date-sessions-modal');
        const dateCloseBtn = document.getElementById('date-modal-close-btn');
        
        console.log('Date modal elements for listeners:', {
            dateModal: !!dateModal,
            dateCloseBtn: !!dateCloseBtn
        });
        
        if (dateCloseBtn) {
            // Remove any existing listeners first
            dateCloseBtn.removeEventListener('click', closeDateSessionsModal);
            // Add the new listener
            dateCloseBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Date modal close button clicked');
                closeDateSessionsModal();
            });
            console.log('Date modal close button listener added');
        } else {
            console.error('Date modal close button not found!');
        }
        
        // Close modal when clicking outside
        if (dateModal) {
            dateModal.addEventListener('click', function(e) {
                if (e.target === dateModal) {
                    console.log('Date modal clicked outside, closing');
                    closeDateSessionsModal();
                }
            });
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

// Unavailability functionality
let currentUnitId = null;
let currentUnit = null;
let unavailabilityData = [];

function initUnavailabilityView() {
    console.log('Initializing unavailability view');
    
    // Get current unit from window data
    if (window.currentUnit) {
        currentUnitId = window.currentUnit.id;
        currentUnit = window.currentUnit;
    } else {
        console.error('No current unit found');
        return;
    }
    
    // Update unit information display
    updateUnitInfo();
    
    // Load unavailability data
    loadUnavailabilityData();
    
    // Initialize calendar
    initUnavailabilityCalendar();
    
    // Initialize modal functionality
    initUnavailabilityModal();
    
    // Initialize additional functionality
    initUnavailabilityControls();
    
    // Initialize advanced modal features
    initAdvancedModalFeatures();
    
    // Initialize AJAX features
    initializeAJAXFeatures();
    
}

function updateUnavailabilityViewForUnit(unit) {
    console.log('Updating unavailability view for unit:', unit.code);
    console.log('Unit data:', unit);
    console.log('Unit start_date:', unit.start_date);
    console.log('Unit end_date:', unit.end_date);
    
    // Update current unit information
    currentUnitId = unit.id;
    currentUnit = {
        id: unit.id,
        code: unit.code,
        name: unit.name,
        start_date: unit.start_date,
        end_date: unit.end_date
    };
    
    console.log('Updated currentUnit:', currentUnit);
    
    // Update unit information display in unavailability view
    updateUnitInfo();
    
    // Reload unavailability data for the new unit
    loadUnavailabilityData();
    
    // Regenerate calendar with new unit data
    regenerateUnavailabilityCalendar();
    
    
    // Update recent unavailability list
    updateRecentUnavailabilityList();
}

function updateUnitInfo() {
    if (!currentUnit) {
        console.log('updateUnitInfo: No currentUnit available');
        return;
    }
    
    console.log('updateUnitInfo: Updating with currentUnit:', currentUnit);
    
    // Update the date range display element
    const unitDateRangeDisplayElement = document.getElementById('unit-date-range-display');
    
    if (unitDateRangeDisplayElement) {
        if (currentUnit.start_date && currentUnit.end_date) {
            const startDate = new Date(currentUnit.start_date);
            const endDate = new Date(currentUnit.end_date);
            const formattedStart = startDate.toLocaleDateString('en-GB');
            const formattedEnd = endDate.toLocaleDateString('en-GB');
            const dateRangeText = `${formattedStart} - ${formattedEnd}`;
            
            console.log('updateUnitInfo: Setting date range to:', dateRangeText);
            unitDateRangeDisplayElement.textContent = dateRangeText;
        } else {
            console.log('updateUnitInfo: No start_date or end_date available');
            unitDateRangeDisplayElement.textContent = 'No date range';
        }
    } else {
        console.log('updateUnitInfo: unit-date-range-display element not found');
    }
}

function loadUnavailabilityData() {
    if (!currentUnitId) {
        console.error('No current unit ID available');
        return;
    }
    
    fetch(`/facilitator/unavailability?unit_id=${currentUnitId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading unavailability:', data.error);
                return;
            }
            
            unavailabilityData = data.unavailabilities || [];
            updateCalendarDisplay();
            updateRecentUnavailabilityList();
        })
        .catch(error => {
            console.error('Error loading unavailability data:', error);
        });
}

function initUnavailabilityCalendar() {
    const calendarDays = document.getElementById('unavailability-calendar-days');
    if (!calendarDays) return;
    
    // Generate calendar for current month
    generateCalendar();
    
    // Add click handlers for calendar days (only if not already added)
    if (!calendarDays.hasAttribute('data-listeners-added')) {
        calendarDays.addEventListener('click', function(e) {
            const dayElement = e.target.closest('.calendar-day');
            if (!dayElement) return;
            
            const date = dayElement.dataset.date;
            if (!date) return;
            
            // Check if date is within unit period
            if (!isDateInUnitPeriod(date)) {
                alert('You can only set unavailability for dates within the unit period');
                return;
            }
            
            // Open modal for this date
            openUnavailabilityModal(date);
        });
        
        calendarDays.setAttribute('data-listeners-added', 'true');
    }
}

function regenerateUnavailabilityCalendar() {
    // Generate calendar for current month without re-adding event listeners
    generateCalendar();
}

function generateCalendar() {
    const calendarDays = document.getElementById('unavailability-calendar-days');
    if (!calendarDays) return;
    
    // Get current calendar state
    const currentDate = window.calendarCurrentDate || new Date();
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Update month title
    const monthTitle = document.getElementById('current-month-unavailability');
    if (monthTitle) {
        monthTitle.textContent = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    }
    
    // Clear existing days
    calendarDays.innerHTML = '';
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        calendarDays.appendChild(emptyDay);
    }
    
    // Add days of month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = day;
        
        const date = new Date(year, month, day);
        const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        dayElement.dataset.date = dateString;
        
        // Check if date is in unit period
        if (isDateInUnitPeriod(dateString)) {
            dayElement.classList.add('unit-period');
        } else {
            dayElement.classList.add('outside-period');
        }
        
        // Check if date has unavailability
        if (hasUnavailability(dateString)) {
            dayElement.classList.add('unavailable');
        }
        
        // Add today indicator
        const today = new Date();
        const todayString = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        if (dateString === todayString) {
            dayElement.classList.add('today');
        }
        
        calendarDays.appendChild(dayElement);
    }
    
    // Update calendar display after generation
    updateCalendarDisplay();
}

function isDateInUnitPeriod(dateString) {
    if (!currentUnit || !currentUnit.start_date || !currentUnit.end_date) return false;
    
    const date = new Date(dateString);
    const startDate = new Date(currentUnit.start_date);
    const endDate = new Date(currentUnit.end_date);
    
    return date >= startDate && date <= endDate;
}

function hasUnavailability(dateString) {
    return unavailabilityData.some(unav => unav.date === dateString);
}

function updateCalendarDisplay() {
    const calendarDays = document.querySelectorAll('.calendar-day');
    calendarDays.forEach(dayElement => {
        const date = dayElement.dataset.date;
        if (!date) return;
        
        dayElement.classList.remove('unavailable');
        if (hasUnavailability(date)) {
            dayElement.classList.add('unavailable');
        }
    });
}

function openUnavailabilityModal(date) {
    const modal = document.getElementById('unavailability-modal');
    const subtitle = document.getElementById('modal-date-subtitle');
    
    if (!modal || !subtitle) return;
    
    // Update modal subtitle
    const dateObj = new Date(date);
    const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
    const formattedDate = dateObj.toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric', 
        year: 'numeric' 
    });
    subtitle.textContent = `Configure your unavailable times for ${dayName}, ${formattedDate}`;
    
    // Store current date for saving
    modal.dataset.currentDate = date;
    
    // Reset form
    resetUnavailabilityForm();
    
    // Show modal
    modal.style.display = 'flex';
}

function resetUnavailabilityForm() {
    document.getElementById('full-day-toggle').checked = false;
    document.getElementById('recurring-toggle').checked = false;
    document.getElementById('repeat-every').value = 'weekly';
    document.getElementById('custom-recurrence').style.display = 'none';
    document.getElementById('recurring-options').style.display = 'none';
    document.getElementById('until-date').value = '';
    document.getElementById('unavailability-reason').value = '';
    
    // Clear time ranges
    const container = document.getElementById('time-ranges-container');
    container.innerHTML = '<div class="no-time-ranges"><span class="material-icons">schedule</span><p>No specific time ranges set. Click \'Add Time Range\' to specify unavailable hours</p></div>';
}

function initUnavailabilityModal() {
    const modal = document.getElementById('unavailability-modal');
    const closeBtn = document.getElementById('unavailability-modal-close');
    const cancelBtn = document.getElementById('cancel-unavailability');
    const saveBtn = document.getElementById('save-unavailability');
    const fullDayToggle = document.getElementById('full-day-toggle');
    const recurringToggle = document.getElementById('recurring-toggle');
    const repeatEverySelect = document.getElementById('repeat-every');
    const addTimeRangeBtn = document.getElementById('add-time-range');
    
    // Close modal function
    function closeModal() {
        modal.style.display = 'none';
        resetUnavailabilityForm();
    }
    
    // Close modal handlers
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    
    // Close on overlay click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) closeModal();
    });
    
    // Full day toggle functionality
    if (fullDayToggle) {
        fullDayToggle.addEventListener('change', function() {
            const timeRangesContainer = document.getElementById('time-ranges-container');
            const addTimeRangeBtn = document.getElementById('add-time-range');
            
            if (this.checked) {
                // Hide time ranges when full day is selected
                timeRangesContainer.style.display = 'none';
                if (addTimeRangeBtn) addTimeRangeBtn.style.display = 'none';
            } else {
                // Show time ranges when partial day is selected
                timeRangesContainer.style.display = 'block';
                if (addTimeRangeBtn) addTimeRangeBtn.style.display = 'block';
                
                // Add default time range if none exist
                if (timeRangesContainer.children.length === 0) {
                    addTimeRange();
                }
            }
        });
    }
    
    // Recurring toggle functionality
    if (recurringToggle) {
        recurringToggle.addEventListener('change', function() {
            const recurringOptions = document.getElementById('recurring-options');
            
            if (this.checked) {
                recurringOptions.style.display = 'block';
            } else {
                recurringOptions.style.display = 'none';
            }
        });
    }
    
    // Repeat every select functionality
    if (repeatEverySelect) {
        repeatEverySelect.addEventListener('change', function() {
            const customRecurrence = document.getElementById('custom-recurrence');
            
            if (this.value === 'custom') {
                customRecurrence.style.display = 'block';
            } else {
                customRecurrence.style.display = 'none';
            }
        });
    }
    
    // Add time range functionality
    if (addTimeRangeBtn) {
        addTimeRangeBtn.addEventListener('click', addTimeRange);
    }
    
    // Save unavailability functionality
    if (saveBtn) {
        saveBtn.addEventListener('click', saveUnavailability);
    }
}

function addTimeRange() {
    const container = document.getElementById('time-ranges-container');
    
    // Remove "no time ranges" message
    const noTimeRanges = container.querySelector('.no-time-ranges');
    if (noTimeRanges) {
        noTimeRanges.remove();
    }
    
    const timeRangeDiv = document.createElement('div');
    timeRangeDiv.className = 'time-range-item';
    
    timeRangeDiv.innerHTML = `
        <div class="time-range-controls">
            <div class="time-input-group">
                <label>Start Time</label>
                <input type="time" class="time-input" value="09:00">
            </div>
            <div class="time-input-group">
                <label>End Time</label>
                <input type="time" class="time-input" value="17:00">
            </div>
            <button class="remove-time-range" type="button">
                <span class="material-icons">delete</span>
            </button>
        </div>
    `;
    
    container.appendChild(timeRangeDiv);
    
    // Add event listeners for the new time range
    const removeBtn = timeRangeDiv.querySelector('.remove-time-range');
    
    // Remove button functionality
    removeBtn.addEventListener('click', function() {
        timeRangeDiv.remove();
        
        // Show "no time ranges" message if no ranges left
        if (container.children.length === 0) {
            container.innerHTML = '<div class="no-time-ranges"><span class="material-icons">schedule</span><p>No specific time ranges set. Click \'Add Time Range\' to specify unavailable hours</p></div>';
        }
    });
}

function saveUnavailability() {
    const modal = document.getElementById('unavailability-modal');
    const date = modal.dataset.currentDate;
    
    if (!date || !currentUnitId) return;
    
    const isFullDay = document.getElementById('full-day-toggle').checked;
    const isRecurring = document.getElementById('recurring-toggle').checked;
    const reason = document.getElementById('unavailability-reason').value;
    
    let startTime = null;
    let endTime = null;
    
    if (!isFullDay) {
        const timeRanges = document.querySelectorAll('.time-range-item');
        if (timeRanges.length > 0) {
            // For now, just use the first time range
            const firstRange = timeRanges[0];
            const startInput = firstRange.querySelector('input[type="time"]');
            const endInput = firstRange.querySelectorAll('input[type="time"]')[1];
            startTime = startInput.value;
            endTime = endInput.value;
        }
    }
    
    const data = {
        unit_id: currentUnitId,
        date: date,
        is_full_day: isFullDay,
        start_time: startTime,
        end_time: endTime,
        reason: reason
    };
    
    if (isRecurring) {
        data.recurring_pattern = document.getElementById('repeat-every').value;
        data.recurring_end_date = document.getElementById('until-date').value;
        
        const customInterval = document.getElementById('custom-interval');
        if (customInterval && customInterval.value) {
            data.recurring_interval = parseInt(customInterval.value);
        }
    }
    
    fetch('/facilitator/unavailability', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert('Error saving unavailability: ' + result.error);
            return;
        }
        
        // Reload unavailability data
        loadUnavailabilityData();
        
        // Close modal
        modal.style.display = 'none';
        
        console.log('Unavailability saved successfully');
    })
    .catch(error => {
        console.error('Error saving unavailability:', error);
        alert('Error saving unavailability');
    });
}

// Additional unavailability functionality
function initUnavailabilityControls() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-unavailability');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadUnavailabilityData();
            generateCalendar();
            updateRecentUnavailabilityList();
        });
    }
    
    // Calendar navigation
    const prevBtn = document.getElementById('prev-month-unavailability');
    const nextBtn = document.getElementById('next-month-unavailability');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            navigateCalendar(-1);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            navigateCalendar(1);
        });
    }
}

function updateRecentUnavailabilityList() {
    const listContainer = document.getElementById('recent-unavailability-list');
    if (!listContainer) return;
    
    if (unavailabilityData.length === 0) {
        listContainer.innerHTML = `
            <div class="no-unavailability">
                <span class="material-icons">event_available</span>
                <p>No unavailability set yet. Click on calendar dates to get started.</p>
            </div>
        `;
        return;
    }
    
    // Sort by date (most recent first) and take first 5
    const recentUnavailability = unavailabilityData
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 5);
    
    listContainer.innerHTML = recentUnavailability.map(unav => {
        const date = new Date(unav.date);
        const formattedDate = date.toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
        });
        
        let timeInfo = '';
        if (unav.is_full_day) {
            timeInfo = '<span class="time-info full-day">Full Day</span>';
        } else if (unav.start_time && unav.end_time) {
            timeInfo = `<span class="time-info partial">${unav.start_time} - ${unav.end_time}</span>`;
        }
        
        let recurringInfo = '';
        if (unav.recurring_pattern) {
            recurringInfo = `<span class="recurring-info">${unav.recurring_pattern}</span>`;
        }
        
        return `
            <div class="unavailability-item">
                <div class="item-date">
                    <span class="material-icons">event_busy</span>
                    <span class="date-text">${formattedDate}</span>
                </div>
                <div class="item-details">
                    ${timeInfo}
                    ${recurringInfo}
                </div>
                <div class="item-actions">
                    <button class="edit-btn" onclick="editUnavailability(${unav.id})">
                        <span class="material-icons">edit</span>
                    </button>
                    <button class="delete-btn" onclick="deleteUnavailability(${unav.id})">
                        <span class="material-icons">delete</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function navigateCalendar(direction) {
    // Initialize calendar current date if not set
    if (!window.calendarCurrentDate) {
        window.calendarCurrentDate = new Date();
    }
    
    // Navigate to previous/next month
    const currentDate = window.calendarCurrentDate;
    const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + direction, 1);
    
    // Update calendar current date
    window.calendarCurrentDate = newDate;
    
    // Regenerate calendar
    generateCalendar();
}

function editUnavailability(unavailabilityId) {
    // Find the unavailability record
    const unav = unavailabilityData.find(u => u.id === unavailabilityId);
    if (!unav) return;
    
    // Open the modal with existing data
    openUnavailabilityModal(unav.date);
    
    // Pre-populate the form with existing data
    setTimeout(() => {
        populateUnavailabilityForm(unav);
    }, 100);
}

function deleteUnavailability(unavailabilityId) {
    if (!confirm('Are you sure you want to delete this unavailability?')) {
        return;
    }
    
    fetch(`/facilitator/unavailability/${unavailabilityId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': window.csrfToken
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert('Error deleting unavailability: ' + result.error);
            return;
        }
        
        // Reload unavailability data
        loadUnavailabilityData();
        console.log('Unavailability deleted successfully');
    })
    .catch(error => {
        console.error('Error deleting unavailability:', error);
        alert('Error deleting unavailability');
    });
}

function populateUnavailabilityForm(unav) {
    // Pre-populate the modal form with existing unavailability data
    const fullDayToggle = document.getElementById('full-day-toggle');
    const recurringToggle = document.getElementById('recurring-toggle');
    const reasonField = document.getElementById('unavailability-reason');
    
    if (fullDayToggle) fullDayToggle.checked = unav.is_full_day;
    if (recurringToggle) recurringToggle.checked = !!unav.recurring_pattern;
    if (reasonField) reasonField.value = unav.reason || '';
    
    // Handle recurring options
    if (unav.recurring_pattern) {
        const recurringOptions = document.getElementById('recurring-options');
        if (recurringOptions) recurringOptions.style.display = 'block';
        
        const repeatSelect = document.getElementById('repeat-every');
        if (repeatSelect) repeatSelect.value = unav.recurring_pattern;
        
        const untilDate = document.getElementById('until-date');
        if (untilDate && unav.recurring_end_date) {
            untilDate.value = unav.recurring_end_date;
        }
    }
    
    // Handle time ranges
    if (!unav.is_full_day && unav.start_time && unav.end_time) {
        const container = document.getElementById('time-ranges-container');
        container.innerHTML = `
            <div class="time-range-item">
                <div class="time-range-controls">
                    <div class="time-input-group">
                        <label>Start Time</label>
                        <input type="time" class="time-input" value="${unav.start_time}">
                    </div>
                    <div class="time-input-group">
                        <label>End Time</label>
                        <input type="time" class="time-input" value="${unav.end_time}">
                    </div>
                    <button class="remove-time-range" type="button">
                        <span class="material-icons">delete</span>
                    </button>
                </div>
            </div>
        `;
    }
}

// Placeholder functions for advanced features
function initAdvancedModalFeatures() {
    // Advanced options toggle
    const toggleAdvancedBtn = document.getElementById('toggle-advanced');
    const advancedOptions = document.getElementById('advanced-options');
    
    if (toggleAdvancedBtn && advancedOptions) {
        toggleAdvancedBtn.addEventListener('click', function() {
            const isVisible = advancedOptions.style.display !== 'none';
            advancedOptions.style.display = isVisible ? 'none' : 'block';
            
            const icon = toggleAdvancedBtn.querySelector('.material-icons');
            icon.textContent = isVisible ? 'expand_more' : 'expand_less';
        });
    }
}

function initializeAJAXFeatures() {
    // Set up global error handling
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
    });
}
