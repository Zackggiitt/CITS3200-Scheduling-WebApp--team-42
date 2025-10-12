# Multi-Facilitator UI Implementation

## Overview

This implementation updates the user interface to properly display multiple facilitators assigned to sessions, showing both lead and support staff with their respective roles. The UI now reflects the bulk staffing configuration set by unit coordinators.

## Changes Made

### 1. Backend API Updates (`unitcoordinator_routes.py`)

#### Enhanced `_serialize_session()` Function
Updated to return comprehensive facilitator information:

```python
# Get all facilitator information with roles
facilitators = []
if s.assignments:
    for assignment in s.assignments:
        if assignment.facilitator:
            facilitator_info = {
                "id": assignment.facilitator.id,
                "name": f"{assignment.facilitator.first_name} {assignment.facilitator.last_name}",
                "email": assignment.facilitator.email,
                "role": getattr(assignment, 'role', 'lead'),  # 'lead' or 'support'
                "is_confirmed": assignment.is_confirmed
            }
            facilitators.append(facilitator_info)
```

#### Key Features:
- **All facilitators included**: Returns all assigned facilitators, not just the first one
- **Role information**: Each facilitator includes their role (lead/support)
- **Confirmation status**: Tracks whether each facilitator has confirmed their assignment
- **Backward compatibility**: Maintains the original `facilitator` field for existing code
- **Smart status**: Session status reflects the overall confirmation state

#### Session Status Logic:
- **Approved**: At least one facilitator has confirmed
- **Pending**: Facilitators assigned but none confirmed yet
- **Unassigned**: No facilitators assigned

### 2. Frontend JavaScript Updates (`static/js/uc.js`)

#### Session List View
Updated to display all facilitators with role badges:

```javascript
${session.facilitators?.length > 0 
  ? session.facilitators.map(f => {
      const roleBadge = f.role === 'lead' 
        ? '<span class="role-badge lead">Lead</span>' 
        : '<span class="role-badge support">Support</span>';
      return `${f.name || 'Unknown'} ${roleBadge}`;
    }).join(', ')
  : 'None assigned'
}
```

#### Schedule View
Enhanced to show facilitator count and detailed role information:

```javascript
// Header shows facilitator count for multiple facilitators
${session.facilitators?.length > 0 
  ? (session.facilitators.length > 1 
      ? `${session.facilitators.length} Facilitators`
      : getInitials(session.facilitators[0].name))
  : 'Unassigned'
}

// Details section shows all facilitators with roles
${session.facilitators?.map(f => {
  const roleBadge = f.role === 'lead' 
    ? '<span class="role-badge lead">Lead</span>' 
    : '<span class="role-badge support">Support</span>';
  return `${f.name} ${roleBadge}`;
}).join(', ')}
```

### 3. CSS Styling (`static/uc.css`)

#### Role Badge Styles
Added visual distinction between lead and support roles:

```css
.role-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 4px;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.role-badge.lead {
  background-color: #dbeafe;  /* Blue background */
  color: #1e40af;            /* Blue text */
  border: 1px solid #93c5fd;
}

.role-badge.support {
  background-color: #f3f4f6;  /* Gray background */
  color: #374151;            /* Gray text */
  border: 1px solid #d1d5db;
}
```

### 4. Facilitator Dashboard Updates (`facilitator_routes.py`)

#### Enhanced Session Data
Updated facilitator dashboard to include role information in session assignments:

```python
'role': getattr(a, 'role', 'lead')  # Include role information
```

This allows facilitators to see whether they are assigned as lead or support staff for each session.

## UI Display Examples

### Session List View
**Before:**
```
Facilitator: Quinn Gonzalez
```

**After:**
```
Facilitators: Alice Expert Lead, Bob Senior Support
```

### Schedule View
**Before:**
```
Session: Workshop-05_Pipeworks_and_Tour-05
Facilitator: QG (Quinn Gonzalez)
```

**After:**
```
Session: Workshop-05_Pipeworks_and_Tour-05
Facilitators: 2 Facilitators
Details:
  👤 Alice Expert Lead, Bob Senior Support
```

### Large Session Example
```
Session: Advanced Lab Session
Facilitators: 3 Facilitators
Details:
  👤 Alice Expert Lead, Bob Senior Lead, Carol Mid Support
```

## Visual Design

### Role Badge Colors
- **Lead Badge**: Blue background (#dbeafe) with blue text (#1e40af)
- **Support Badge**: Gray background (#f3f4f6) with gray text (#374151)

### Layout Considerations
- **Compact Display**: Role badges are small and inline to save space
- **Clear Hierarchy**: Lead roles are visually more prominent than support roles
- **Consistent Spacing**: 4px margin between name and role badge
- **Accessibility**: High contrast colors and clear text

## Backward Compatibility

The implementation maintains full backward compatibility:

1. **Original API Fields**: The `facilitator` field still returns the first facilitator's name
2. **Existing Code**: All existing JavaScript and templates continue to work
3. **Gradual Enhancement**: New features are additive, not replacing existing functionality

## Testing

Created comprehensive test suite (`test_multi_facilitator_display.py`) that verifies:

1. **Single facilitator sessions** (1 lead)
2. **Multiple facilitator sessions** (1 lead, 1 support)
3. **Large sessions** (2 leads, 1 support)
4. **Empty sessions** (no facilitators)
5. **Backward compatibility** (original facilitator field)
6. **Status determination** (approved/pending/unassigned)

✅ **All tests passed successfully**

## User Experience Improvements

### For Unit Coordinators
- **Clear visibility** of all assigned staff per session
- **Role identification** helps verify correct staffing levels
- **Status tracking** shows which facilitators have confirmed

### For Facilitators
- **Role awareness** helps understand their responsibilities
- **Team visibility** shows who else is working on the session
- **Confirmation status** indicates whether assignments are finalized

### For Administrators
- **Complete picture** of session staffing
- **Role distribution** helps assess workload balance
- **Confirmation tracking** aids in schedule management

## Implementation Notes

### Data Flow
1. **Database**: Assignment records include role field
2. **Backend**: `_serialize_session()` extracts all facilitator data with roles
3. **Frontend**: JavaScript renders role badges and facilitator lists
4. **CSS**: Styling provides visual distinction between roles

### Performance Considerations
- **Minimal overhead**: Role information is included in existing API calls
- **Efficient rendering**: Role badges are simple HTML elements
- **Cached styling**: CSS classes are lightweight and reusable

### Future Enhancements
Potential improvements for future versions:

1. **Role-based permissions**: Different UI access based on lead/support role
2. **Role preferences**: Allow facilitators to prefer certain roles
3. **Role switching**: UI for changing facilitator roles
4. **Enhanced filtering**: Filter sessions by role type
5. **Role statistics**: Dashboard metrics showing role distribution

## Summary

The multi-facilitator UI implementation successfully addresses the user's requirement to "show who the support facilitators are or other lead facilitators if any." The system now:

- ✅ **Displays all facilitators** assigned to each session
- ✅ **Shows role information** (Lead/Support) with visual badges
- ✅ **Maintains backward compatibility** with existing code
- ✅ **Provides clear visual hierarchy** between lead and support roles
- ✅ **Works across all views** (list, schedule, dashboard)
- ✅ **Includes comprehensive testing** to ensure reliability

The implementation is production-ready and provides a much clearer view of session staffing for all users of the system.
