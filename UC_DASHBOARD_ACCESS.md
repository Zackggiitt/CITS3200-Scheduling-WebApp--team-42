# Unit Coordinator Dashboard Access Guide

This guide explains how to access the unit coordinator dashboard in the main branch.

## Prerequisites

- Python 3.x installed
- Virtual environment activated (if using one)
- All dependencies installed (`pip install -r requirements.txt`)

## Quick Setup Process

### Step 1: Set Password for Test Coordinator

The test data script creates the coordinator user but doesn't set a password. You need to set one using the `add_admin.py` script:

```bash
python add_uc.py --email uc_demo@example.com --password your_password_here
```

**Recommended password:** `password123` (for easy testing)

### Step 2: Start the Application

```bash
python application.py
```

The application will start on `http://localhost:5001`

### Step 3: Access Unit Coordinator Dashboard

1. Open your browser and go to `http://localhost:5001`
2. You'll be redirected to the login page
3. **Login credentials:**
   - **Email:** `uc_demo@example.com`
   - **Password:** `password123` (or whatever you set in Step 2)
   - **Role:** Select "Unit Coordinator" from the dropdown
4. Click "Login"
5. You'll be automatically redirected to the unit coordinator dashboard

## Creating a New Unit

### Step-by-Step Process

#### Step 1: Basic Information

1. **Click "Create Unit"** button in the header
2. **Fill in unit details:**
   - Unit code (e.g., CITS1001)
   - Unit name (e.g., Computer Science Fundamentals)
   - Semester (e.g., Semester 1, 2025)
   - Year (e.g., 2025)
   - Start date and end date
3. **Click "Next"** to proceed

#### Step 2: Date Range Selection

1. **Select teaching period dates** using date pickers
2. **Choose start and end dates** for the unit
3. **Review date summary** showing selected range
4. **Click "Next"** to continue

#### Step 3A: Upload Data Files

1. **Upload Sessions CSV:**
   - Format: session_name, day, start_time, end_time, venue, module
   - Example: "Lab 1, Monday, 09:00, 11:00, Lab A, CITS1001_Lab"
2. **Upload CAS CSV:**
   - Course Allocation System data
   - Contains official university timetable information
3. **Verify upload status** (success/error messages)
4. **Click "Next"** when uploads are complete

#### Step 3B: Calendar Setup

1. **Review uploaded sessions** in calendar view
2. **Assign venues** using dropdown selectors
3. **Set staffing requirements:**
   - Lead facilitator count
   - Support facilitator count
4. **Adjust session times** if needed
5. **Click "Next"** to proceed

#### Step 4: Review & Confirm

1. **Review all unit information:**
   - Basic details
   - Date range
   - Session count
   - Venue assignments
2. **Verify session schedule** in calendar view
3. **Click "Create Unit"** to finalise
4. **Success confirmation** appears

## What You'll See in the Dashboard

The unit coordinator dashboard includes:

- #### 1. Dashboard Tab 
  - **Schedule Overview:** Statistics cards showing total schedule, assigned sessions, conflicts, and facilitator count
  - **Session Overview Widget:** Two main sections:
    - **Today's Sessions:** Real-time list of today's sessions with status indicators
    - **Upcoming Sessions:** Week view with mini calendar and upcoming session list
  - **Attendance Summary:** Visual gauge showing attendance metrics
  - **Activity Log:** Recent activity tracking with facilitator data

  #### 2. Schedule Tab 
  - **View Toggle:** Switch between Calendar View and List View
  - **Course Information:** Unit details with auto-assign facilitator button
  - **Week Navigation:** Navigate through different weeks
  - **Status Legend:** Colour-coded status indicators (Approved, Pending, Unassigned, Proposed)
  - **Calendar Grid:** 7-day week view with session cards
  - **Session Statistics:** Cards showing total, approved, pending, and unassigned sessions
  - **Filters & Search:** Search by activity, location, facilitator, or module
  - **Sorting Options:** Sort by time, title, facilitator, or status

  #### 3. Facilitators Tab 
  - **Staffing Statistics:** Total sessions, fully staffed, needs lead, unstaffed
  - **Facilitator Setup Progress:** Progress bars for account setup, availability, and readiness
  - **Facilitator Details:** Comprehensive list with:
    - Contact information
    - Skills and qualifications
    - Account status
    - Availability settings
    - Action buttons for management

  #### 4. Swap & Approvals Tab 
  - **Pending Approvals:** Badge showing number of pending requests
  - **Swap Queue:** Visual representation of session swaps
  - **Approval Actions:** Approve or reject swap requests
  - **Priority Indicators:** High-priority requests highlighted




## Schedule Management Tab

### Calendar View Features

- **Week Grid:** 7-column layout showing Monday through Friday
- **Session Cards:** Each session displayed as a card with:
  - Session name and time
  - Facilitator assignment
  - Status indicator
  - Venue information
- **Status Colours:**
  - 🟢 Green: Approved sessions
  - 🟡 Yellow: Pending approval
  - 🔵 Blue: Proposed assignments
  - ⚪ Gray: Unassigned sessions

### List View Features

- **Session Statistics:** Overview cards with counts
- **Advanced Filtering:** Filter by status, day, or custom criteria
- **Search Functionality:** Find sessions by name, facilitator, or location
- **Sorting Options:** Sort by time, title, facilitator, or status
- **Session Details:** Comprehensive information for each session

### Auto-Assignment

- **Auto-Assign Button:** Automatically assign facilitators to sessions
- **Smart Matching:** Considers facilitator availability and skills
- **Conflict Detection:** Identifies scheduling conflicts
- **Manual Override:** Ability to manually adjust assignments

## Facilitator Management Tab

### Facilitator Overview

- **Total Count:** Number of facilitators assigned to the unit
- **Setup Progress:** Track completion of account setup and availability
- **Status Categories:**
  - Account Setup: Facilitators who have completed registration
  - Availability Set: Facilitators who have set their availability
  - Fully Ready: Facilitators ready for assignment

### Facilitator Details

Each facilitator card shows:
- **Contact Information:** Name, email, phone
- **Skills:** Programming languages, teaching experience
- **Account Status:** Active, pending, or needs setup
- **Availability:** Current availability settings
- **Action Buttons:** Edit, view profile, manage availability

### Bulk Operations

- **Bulk Staffing:** Assign multiple facilitators to sessions
- **Filter Options:** Filter by skills, availability, or status
- **Respect Overrides:** Option to maintain existing assignments

## Swap & Approvals Tab

### Swap Requests

- **Visual Queue:** Chart showing swap request trends
- **Request Details:** Information about requested swaps
- **Priority System:** High-priority requests highlighted
- **Status Tracking:** Track approval status

### Approval Process

1. **Review Request:** Examine swap details and reasoning
2. **Check Conflicts:** Verify no scheduling conflicts
3. **Approve/Reject:** Make decision with single click
4. **Notification:** Automatic notification to facilitators

## Account Settings

### Profile Management

- **Personal Information:** Update name, email, contact details
- **Password Change:** Secure password update
- **Preferences:** Customize dashboard settings
- **Notifications:** Manage notification preferences

### Security Features

- **CSRF Protection:** Built-in security against cross-site attacks
- **Session Management:** Secure session handling
- **Role-Based Access:** Proper permission controls

## Troubleshooting

### Issue: "Invalid credentials" when logging in
**Solution:** Make sure you've set the password using `add_uc.py` after creating the test data.

## Development Notes

- The test data includes realistic date ranges (past and future units)
- Sessions are distributed across different time slots and modules
- Sample unavailability records are created for testing
- Swap requests include various statuses for comprehensive testing
- All data is created with proper foreign key relationships
- Dashboard includes both active and completed units for testing

## Security Note

**Important:** The test passwords (`password123`) are for development/testing only. Never use these credentials in production environments.

---

