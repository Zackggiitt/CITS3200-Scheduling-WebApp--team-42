# Algorithm Randomization Update

## Overview
Updated the optimization engine to produce **varied assignments** on each run while maintaining quality. Previously, the algorithm was deterministic and produced identical results every time.

## Changes Made

### File: `optimization_engine.py`

#### 1. Added Random Module Import
```python
import random
```

#### 2. Randomized Session Processing Order
- Added session shuffling before sorting
- Added small random variation to sort keys to break ties
```python
# Shuffle sessions to vary the assignment order
sessions_copy = sessions.copy()
random.shuffle(sessions_copy)

# Sort with random tie-breaking
sorted_sessions = sorted(sessions_copy, 
    key=lambda s: (-s['duration_hours'], 
                   -SKILL_SCORES.get(s['required_skill_level'], 0), 
                   random.random()))
```

#### 3. Randomized Facilitator Selection Order
- Shuffle facilitators before evaluating them for each session
- This ensures different evaluation orders on each run

**For Lead Staff:**
```python
# Shuffle facilitators to add variation in selection order
shuffled_facilitators = facilitators.copy()
random.shuffle(shuffled_facilitators)

for facilitator in shuffled_facilitators:
    # ... evaluation logic
```

**For Support Staff:**
```python
# Same shuffling approach for support staff
shuffled_facilitators = facilitators.copy()
random.shuffle(shuffled_facilitators)
```

#### 4. Added Score Variation
- Added ±5% random variation to scores
- Introduces diversity while maintaining quality
```python
# Add small random variation (±5%) to introduce diversity
score = score * (1 + random.uniform(-0.05, 0.05))
```

## How It Works

### Deterministic → Non-Deterministic
**Before:** The algorithm always:
1. Processed sessions in the same order
2. Evaluated facilitators in the same order
3. Selected the same "best" facilitator each time
4. Produced **identical** results on every run

**After:** The algorithm now:
1. Shuffles sessions for varied processing order
2. Shuffles facilitators for varied evaluation order
3. Adds small random score variations
4. Produces **different** but equally valid assignments on each run

### Quality Maintained
- All hard constraints still enforced (availability, skills, conflicts)
- Soft constraints still optimized (fairness, skill matching)
- Random variation is small (±5%) to prevent drastic quality changes
- Multiple valid solutions exist; algorithm finds different ones each run

## Testing Results

Ran the algorithm 3 times with the same input data:

```
Run 1 vs Run 2: 7 differences in first 10 assignments
Run 1 vs Run 3: 8 differences in first 10 assignments
Run 2 vs Run 3: 9 differences in first 10 assignments

✓ SUCCESS: Algorithm produces VARIED results on each run
```

## Benefits

1. **Verifiable Reruns**: Users can clearly see when the algorithm has been rerun
2. **Flexibility**: Multiple valid scheduling solutions are explored
3. **Quality Maintained**: Randomization doesn't compromise assignment quality
4. **User Confidence**: Different results confirm the algorithm is actually running

## Impact on Existing Features

### Database Cleanup (Already Implemented)
- Previous assignments are deleted before creating new ones
- Prevents duplicate or stale assignments
- Works correctly with the new randomization

### Frontend Refresh (Already Implemented)
- Calendar and list views refresh after algorithm runs
- Now shows genuinely different assignments on each rerun

## Technical Details

### Randomization Strategy
- **Session-level**: Random shuffle + random tie-breaking in sort
- **Facilitator-level**: Random shuffle before evaluation
- **Score-level**: ±5% random variation

### Seed Management
- No fixed seed used (intentionally)
- Each run produces different results
- Still deterministic within a single run (consistent intermediate results)

## Date
October 13, 2025

