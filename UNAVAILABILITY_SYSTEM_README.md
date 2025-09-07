# Unavailability System Integration

This document describes the integration of the new unavailability system into the existing facilitator portal.

## Overview

The unavailability system replaces the old availability system with a more flexible, unit-scoped approach that allows facilitators to specify when they are unavailable within specific unit periods.

## Key Features

### 1. Unit-Scoped Unavailability
- Facilitators can only set unavailability within the active date range of their assigned units
- Each unit has its own unavailability settings
- Automatic validation ensures dates are within unit periods

### 2. Flexible Time Management
- **Full Day Unavailability**: Mark entire days as unavailable
- **Partial Day Unavailability**: Specify specific time ranges (e.g., 9:00 AM - 5:00 PM)
- **Multiple Time Ranges**: Add multiple time ranges per day (up to 5)

### 3. Recurring Patterns
- **Weekly**: Repeat every week
- **Monthly**: Repeat every month
- **Custom**: Custom intervals (e.g., every 2 weeks)
- **End Date**: Specify when recurring pattern should stop

### 4. Rich User Interface
- **Calendar View**: Visual calendar showing unavailable dates
- **Interactive Modals**: Easy-to-use forms for setting unavailability
- **Real-time Validation**: Immediate feedback on form inputs
- **Responsive Design**: Works on desktop and mobile devices

## Technical Implementation

### Database Schema

#### New Models

**Unavailability**
```python
class Unavailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    is_full_day = db.Column(db.Boolean, default=False)
    recurring_pattern = db.Column(db.Enum(RecurringPattern), nullable=True)
    recurring_end_date = db.Column(db.Date, nullable=True)
    recurring_interval = db.Column(db.Integer, default=1)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**RecurringPattern Enum**
```python
class RecurringPattern(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    CUSTOM = 'custom'
```

### API Endpoints

#### GET `/facilitator/unavailability?unit_id=<int>`
Retrieves unavailability records for a specific unit.

**Response:**
```json
{
  "unavailabilities": [
    {
      "id": 1,
      "date": "2024-01-15",
      "is_full_day": true,
      "start_time": null,
      "end_time": null,
      "recurring_pattern": "weekly",
      "reason": "Medical appointment"
    }
  ]
}
```

#### POST `/facilitator/unavailability`
Creates a new unavailability record.

**Request:**
```json
{
  "unit_id": 1,
  "date": "2024-01-15",
  "is_full_day": false,
  "start_time": "09:00",
  "end_time": "17:00",
  "recurring_pattern": "weekly",
  "recurring_end_date": "2024-03-15",
  "reason": "Regular weekly commitment"
}
```

#### PUT `/facilitator/unavailability/<int:unavailability_id>`
Updates an existing unavailability record.

#### DELETE `/facilitator/unavailability/<int:unavailability_id>`
Deletes an unavailability record.

#### POST `/facilitator/unavailability/generate-recurring`
Generates multiple unavailability entries based on a recurring pattern.

#### GET `/facilitator/unit-info?unit_id=<int>`
Retrieves unit information for the unavailability system.

### Frontend Components

#### Calendar Component
- Interactive calendar showing unit period and unavailable dates
- Click-to-set functionality for dates within unit period
- Visual indicators for different types of unavailability
- Month navigation and view switching

#### Modal System
- **Main Modal**: Set unavailability for a specific date
- **Bulk Edit Modal**: Set unavailability for multiple dates
- **View All Modal**: View and manage all unavailability records

#### Form Validation
- Real-time validation of time ranges
- Overlap detection for multiple time ranges
- Date range validation within unit periods
- Character limits for reason fields

## Migration Process

### Database Migration
The system includes a migration script that:
1. Drops the old `availability` table
2. Creates the new `unavailability` table
3. Preserves existing data (if migration script is used)

### Code Migration
- Updated facilitator routes to include unavailability endpoints
- Enhanced dashboard template with unavailability tab
- Added comprehensive JavaScript functionality
- Updated CSS with new styling

## Usage Instructions

### For Facilitators

1. **Accessing Unavailability**
   - Navigate to the facilitator dashboard
   - Click on the "Unavailability" tab

2. **Setting Unavailability**
   - Click on any date within the unit period
   - Choose between full day or specific time ranges
   - Optionally set up recurring patterns
   - Add a reason for the unavailability

3. **Managing Existing Records**
   - View recent unavailability in the summary section
   - Edit or delete existing records
   - Use bulk edit for multiple dates

### For Administrators

1. **Monitoring Unavailability**
   - View facilitator unavailability through existing admin interfaces
   - Export unavailability data for scheduling purposes

2. **System Maintenance**
   - Monitor database performance
   - Review recurring patterns for optimization

## Validation Rules

### Date Validation
- Dates must be within the unit's active period
- Recurring end dates must be after the start date
- No duplicate unavailability for the same date

### Time Validation
- End time must be after start time
- Time ranges cannot overlap
- Maximum of 5 time ranges per day

### Content Validation
- Reason field limited to 500 characters
- Recurring interval between 1 and 52
- Valid recurring pattern values only

## Error Handling

### Client-Side
- Real-time form validation
- User-friendly error messages
- Graceful handling of network errors
- Retry mechanisms for failed requests

### Server-Side
- Comprehensive input validation
- Proper HTTP status codes
- Detailed error messages
- Database transaction rollback on errors

## Performance Considerations

### Database
- Indexed foreign keys for fast lookups
- Efficient queries for date ranges
- Proper constraints to prevent duplicates

### Frontend
- Lazy loading of calendar data
- Efficient DOM updates
- Minimal API calls
- Cached unit information

## Security

### Authentication
- All endpoints require facilitator authentication
- Unit access validation for each request
- CSRF protection for form submissions

### Authorization
- Users can only access their own unavailability
- Unit assignment verification
- Proper error handling for unauthorized access

## Testing

### Integration Tests
Run the integration test script:
```bash
python test_unavailability_integration.py
```

### Manual Testing
1. Test calendar interaction
2. Verify form validation
3. Check recurring pattern generation
4. Test bulk operations
5. Validate error handling

## Troubleshooting

### Common Issues

1. **Calendar not loading**
   - Check unit assignment
   - Verify unit has valid date range
   - Check browser console for errors

2. **Form validation errors**
   - Ensure time ranges are valid
   - Check date is within unit period
   - Verify required fields are filled

3. **API errors**
   - Check authentication status
   - Verify unit access permissions
   - Review server logs for details

### Debug Mode
Enable debug logging in the application to get detailed error information.

## Future Enhancements

### Planned Features
- Drag-and-drop calendar interaction
- Advanced recurring patterns (e.g., "every weekday")
- Integration with scheduling system
- Mobile app support
- Notification system for conflicts

### Performance Improvements
- Calendar virtualization for large date ranges
- Background processing for recurring patterns
- Caching strategies for frequently accessed data

## Support

For technical support or questions about the unavailability system:
1. Check this documentation
2. Review the integration test results
3. Check application logs
4. Contact the development team

---

**Version**: 1.0  
**Last Updated**: January 2024  
**Compatibility**: Python 3.8+, Flask 2.0+, SQLAlchemy 1.4+
