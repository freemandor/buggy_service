# E2E Tests for Buggy Service

## User Story #2: Intelligent Ride Assignment Test

This E2E test validates the complete flow from the specification:

### Scenario
- **Buggy 1:** At Bel Air, active
- **Buggy 2:** At Reception, idle (if exists)
- **New Ride:** Beach Bar → Reception, 2 guests

### Expected Behavior
The system should assign the new ride to **Buggy 1** because:
- Buggy 1 ETA to Beach Bar: 120s (BA→BB) + 25s (service time) = **145s**
- Buggy 2 ETA to Beach Bar: 90s (R→BA) + 120s (BA→BB) = **210s**

Buggy 1 can pick up the guests **65 seconds earlier**, so it gets the assignment.

### Test Coverage

The E2E test covers:

1. ✅ **Dispatcher creates ride**
   - Login as dispatcher
   - Fill form with pickup/dropoff/guests/room/name
   - Submit and verify assignment to Buggy #1
   - Check success message contains ride code

2. ✅ **Ride appears in tables**
   - Verify ride shows in recent rides table
   - Verify correct route (Beach Bar → Reception)
   - Verify assigned to Buggy #1

3. ✅ **Driver completes route**
   - Login as driver1
   - View route with pickup and dropoff stops
   - Start each stop
   - Complete each stop
   - Verify "No upcoming stops" after completion

4. ✅ **Manager views metrics**
   - Login as manager
   - Verify total rides count updated
   - Verify ride data is visible

5. ✅ **Error handling**
   - Verify form disables when no active buggies
   - Verify warning message displays

## Prerequisites

Before running tests:

1. **Backend must be running:** http://localhost:8000
2. **Frontend must be running:** http://localhost:5173
3. **Database seeded** with POIs, edges, and users:
   ```bash
   cd backend
   .venv\Scripts\python.exe manage.py seed_pois_and_edges
   ```
4. **User Story #2 scenario set up:**
   ```bash
   .venv\Scripts\python.exe manage.py setup_user_story_2
   ```

**Note:** The `setup_user_story_2` command creates:
- Buggy #2 (idle at Reception)
- Driver #2 (driver2/driver2)
- Ride A for Buggy #1 (3 guests, heading to Beach Bar)

## Running the Tests

### Run all tests (headless)
```bash
npm run test:e2e
```

### Run with UI mode (interactive)
```bash
npm run test:e2e:ui
```

### Run in headed mode (see browser)
```bash
npm run test:e2e:headed
```

### Run specific test file
```bash
npx playwright test e2e/user-story-2.spec.ts
```

### Debug mode
```bash
npx playwright test --debug
```

## Test Output

Successful test output includes:
- ✅ All test steps passing
- ✅ Ride code logged to console
- ✅ Route completion confirmed
- ✅ Final metrics verified

## Notes

- Tests run in **Chromium** by default
- Test database should be reset between runs (or tests should handle existing data)
- Each test logs key information like ride codes and metrics
- Screenshots and traces captured on failure (in `playwright-report/`)

## Viewing Test Reports

After running tests:

```bash
npx playwright show-report
```

This opens an HTML report with:
- Test results
- **Video recordings** of each test
- Screenshots (on failure)
- Traces (on retry)
- Network logs
- Console output

### Video Recordings

Videos are automatically recorded for all tests and saved to:
```
test-results/
  user-story-2-[test-name]-chromium/
    video.webm
```

Videos show:
- Every interaction (clicks, typing, navigation)
- The complete user journey
- Timing of each action

Perfect for:
- Debugging test failures
- Documentation and demos
- Understanding test behavior

