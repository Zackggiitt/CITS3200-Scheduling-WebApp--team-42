# Facilitator Dashboard Access Guide

This guide explains how to access the facilitator dashboard using the test data creation script (`create_unavailability_test_data.py`) in the main branch.

## Prerequisites

- Python 3.x installed
- Virtual environment activated (if using one)
- All dependencies installed (`pip install -r requirements.txt`)

## Quick Setup Process

### Step 1: Create Test Data

Run the test data creation script to set up a complete testing environment:

```bash
python create_unavailability_test_data.py create
```

This script will create:
- ✅ Test facilitator user (`fac_demo@example.com`)
- ✅ Sample units (CITS1001, CITS2002, CITS2200, CITS3000)
- ✅ Modules for each unit (labs, tutorials, workshops, lectures)
- ✅ Sessions with realistic scheduling
- ✅ Unit assignments for the facilitator
- ✅ Session assignments for the facilitator
- ✅ Sample unavailability records
- ✅ Additional facilitators for swap testing
- ✅ Sample swap requests

### Step 2: Set Password for Test Facilitator

The test data script creates the facilitator user but doesn't set a password. You need to set one using the `add_facilitator.py` script:

```bash
python add_facilitator.py --email fac_demo@example.com --password your_password_here
```

**Recommended password:** `password123` (for easy testing)

### Step 3: Start the Application

```bash
python application.py
```

The application will start on `http://localhost:5001`

### Step 4: Access Facilitator Dashboard

1. Open your browser and go to `http://localhost:5001`
2. You'll be redirected to the login page
3. **Login credentials:**
   - **Email:** `fac_demo@example.com`
   - **Password:** `password123` (or whatever you set in Step 2)
   - **Role:** Select "Facilitator" from the dropdown
4. Click "Login"
5. You'll be automatically redirected to the facilitator dashboard

## What You'll See in the Dashboard

The facilitator dashboard includes:

### 📅 **Schedule Management**
- View your assigned sessions
- See upcoming sessions with details (time, location, module)
- Past sessions for reference

### 🚫 **Unavailability Management**
- Set your unavailable dates/times
- View existing unavailability records
- Manage recurring patterns

### 🔄 **Swap Requests**
- Request session swaps with other facilitators
- View pending swap requests
- Accept/decline incoming swap requests
- Track swap request status

### 📊 **Dashboard Overview**
- Summary of your assignments
- Upcoming sessions
- Recent activity

## Test Data Details

### Units Created
- **CITS1001** - Computer Science Fundamentals (Active)
- **CITS2002** - Systems Programming (Active)  
- **CITS2200** - Algorithms and Data Structures (Past)
- **CITS3000** - Software Engineering Project (Past)

### Additional Test Facilitators
- `fac_sarah@example.com` (password: `password123`)
- `fac_michael@example.com` (password: `password123`)
- `fac_emily@example.com` (password: `password123`)

## Useful Commands

### Check Test Data Status
```bash
python create_unavailability_test_data.py status
```

### Clear All Test Data
```bash
python create_unavailability_test_data.py clear
```

### Update Facilitator Password
```bash
python add_facilitator.py --email fac_demo@example.com --password new_password --update
```

## Troubleshooting

### Issue: "Invalid credentials" when logging in
**Solution:** Make sure you've set the password using `add_facilitator.py` after creating the test data.

### Issue: No sessions visible in dashboard
**Solution:** Run `python create_unavailability_test_data.py create` again to ensure all data is properly created.

### Issue: Database errors
**Solution:** Clear the database and recreate:
```bash
python create_unavailability_test_data.py clear
python create_unavailability_test_data.py create
python add_facilitator.py --email fac_demo@example.com --password password123
```

## Development Notes

- The test data includes realistic date ranges (past and future units)
- Sessions are distributed across different time slots
- Sample unavailability records are created for testing
- Swap requests include various statuses for comprehensive testing
- All data is created with proper foreign key relationships

## Security Note

⚠️ **Important:** The test passwords (`password123`) are for development/testing only. Never use these credentials in production environments.

---

**Happy Testing!** 🎉

The facilitator dashboard is now ready for testing all scheduling, unavailability, and swap request features.
