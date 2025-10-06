# Unit Coordinator Dashboard Access Guide

This guide explains how to access the unit coordinator dashboard using the test data creation scripts in the main branch.

## Prerequisites

- Python 3.x installed
- Virtual environment activated (if using one)
- All dependencies installed (`pip install -r requirements.txt`)

## Quick Setup Process

### Step 1: Create Unit Coordinator User

Create a unit coordinator user using the `add_uc.py` script:

```bash
python add_uc.py --email uc_demo@example.com --password password123 
```

**Recommended credentials:**

- **Email:** `uc_demo@example.com`
- **Password:** `password123`

### Step 2: Start the Application

```bash
export FLASK_APP=application.py
flask run
```

The application will start on `http://localhost:5001`

### Step 3: Access Unit Coordinator Dashboard

1. Open your browser and go to `http://localhost:5001`
2. You'll be redirected to the login page
3. **Login credentials:**
   - **Email:** `uc_demo@example.com`
   - **Password:** `password123`
   - **Role:** Select "Unit Coordinator" from the dropdown
4. Click "Login"
5. You'll be automatically redirected to the unit coordinator dashboard



## Creating a New Unit

### Step-by-Step Process

#### Step 1: Basic Information

1. **Click "Create Unit"** button in the header
2. Fill in unit details:
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

1. Upload Sessions CSV:
   - Format: session_name, day, start_time, end_time, venue, module
   - Example: "Lab 1, Monday, 09:00, 11:00, Lab A, CITS1001_Lab"
2. Upload CAS CSV:
   - Course Allocation System data
   - Contains official university timetable information
3. **Verify upload status** (success/error messages)
4. **Click "Next"** when uploads are complete

#### Step 3B: Calendar Setup

1. **Review uploaded sessions** in calendar view
2. **Assign venues** using dropdown selectors
3. Set staffing requirements:
   - Lead facilitator count
   - Support facilitator count
4. **Adjust session times** if needed
5. **Click "Next"** to proceed

#### Step 4: Review & Confirm

1. Review all unit information:
   - Basic details
   - Date range
   - Session count
   - Venue assignments
2. **Verify session schedule** in calendar view
3. **Click "Create Unit"** to finalise
4. **Success confirmation** appears



## What You'll See in the Dashboard

The unit coordinator dashboard includes:

### **Dashboard Overview Tab**

- **Greeting Banner:** Personalised welcome
- **Unit Statistics:** Total sessions, facilitators, completion rates
- **Today's Sessions:** Real-time session tracking with attendance gauges
- **Upcoming Sessions:** Next 7 days of scheduled sessions
- **Attendance Summary:** Table showing attendance hours
- **Swap Queue:** Pending swap requests requiring approval

###  **Schedule Tab**

- **View Toggle:** Switch between Grid View and List View
- **Week Navigation:** Navigate through different weeks
- **Session Grid:** 7-day weekly view with session cards
- **Session Details:** Time, location, facilitator assignments
- **Status Indicators:** Approved, pending, unassigned sessions
- **Auto-Assignment:** Bulk assign facilitators to sessions
- **Session Statistics:** Counts by status type

###  **Facilitators Tab**

- **Facilitator List:** All facilitators with status chips
- **Search & Filter:** Find facilitators by name or skills
- **Status Tracking:** Ready, Active, Pending, Needs Setup
- **Contact Information:** Email and availability details
- **Skill Management:** View facilitator competencies
- **Action Buttons:** Edit, contact, manage availability

### **Swaps & Approvals Tab**

- **Pending Queue:** Swap requests awaiting approval

- **Swap Details:** Complete swap information with reasoning

- **Approval Actions:** Approve or decline requests

- **Priority Handling:** Urgent swaps highlighted

- **Swap History:** Track completed swaps

- **Facilitator Matching:** See who's involved in each swap

  

## Advanced Features

### Unit Creation Wizard

- **Step 1:** Basic unit information (code, name, dates)
- **Step 2:** Date range selection with visual calendar
- **Step 3A:** Upload CSV files for sessions and facilitators
- **Step 3B:** Calendar-based session creation with inspector panel
- **Step 4:** Review and confirm unit creation

### Bulk Operations

- **Bulk Staffing:** Assign multiple facilitators to sessions
- **Bulk Session Creation:** Create multiple sessions at once
- **Bulk Status Updates:** Change multiple session statuses

### Auto-Assignment Features

- **Smart Assignment**: Automatically assign facilitators to unassigned sessions

- **Skill Matching**: Match facilitators based on required skills and competencies

- **Availability Checking:** Consider facilitator availability and unavailability

- **One-Click Assignment**: Bulk assign all unassigned sessions with a single click



## Development Notes

- The test data includes realistic date ranges (past and future units)
- Sessions are distributed across different time slots and days
- Sample unavailability records are created for testing
- Swap requests include various statuses for comprehensive testing
- All data is created with proper foreign key relationships
- Real-time updates for activity and session changes



## Security Note

 **Important:** The test passwords (`password123`, `admin`) are for development/testing only. Never use these credentials in production environments.

---

