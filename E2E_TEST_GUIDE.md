# E2E Test Guide

This project uses **isolated test environments** to ensure E2E tests don't affect your development database or running servers.

## Quick Start

Run E2E tests with a single command:

```powershell
.\run-e2e-tests.ps1
```

## What It Does

The `run-e2e-tests.ps1` script automatically:

1. **Creates a test database** (`backend/test_db.sqlite3`)
   - Uses separate Django settings (`settings_test.py`)
   - Runs migrations
   - Seeds test data

2. **Starts isolated test servers**
   - Backend on port `8001` (dev uses `8000`)
   - Frontend on port `5174` (dev uses `5173`)

3. **Runs Playwright E2E tests**
   - Slow-mo mode for better videos
   - Visual click indicators
   - Complete test isolation

4. **Cleans up automatically**
   - Stops test servers
   - Preserves your development environment

## Files

### Test Configuration
- `backend/buggy_project/settings_test.py` - Test-specific Django settings
- `frontend/playwright.config.test.ts` - Test-specific Playwright config
- `run-e2e-tests.ps1` - Main test runner script

### What's Isolated
✅ **Test database** - Separate `test_db.sqlite3`  
✅ **Backend server** - Different port (8001)  
✅ **Frontend server** - Different port (5174)  
✅ **Test data** - Fresh seed on each run  

### What's NOT Affected
✅ **Development database** - `db.sqlite3` untouched  
✅ **Development servers** - Can run simultaneously  
✅ **Your work** - Tests run in complete isolation  

## Running Tests Manually

If you prefer to run components separately:

### 1. Setup Test Database
```powershell
cd backend
.venv\Scripts\python.exe manage.py migrate --settings=buggy_project.settings_test
.venv\Scripts\python.exe manage.py seed_pois_and_edges --settings=buggy_project.settings_test
```

### 2. Start Test Backend
```powershell
cd backend
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001 --settings=buggy_project.settings_test
```

### 3. Start Test Frontend
```powershell
cd frontend
npm run dev -- --port 5174
```

### 4. Run Playwright Tests
```powershell
cd frontend
npm run test:e2e -- --config playwright.config.test.ts
```

## Test Videos

After tests run, find videos in:
```
frontend/test-results/[test-name]/video.webm
```

Videos include:
- Slow-motion playback (1000ms between actions)
- Visual click indicators (blue ripples)
- Full test flow captured

## Troubleshooting

### Ports Already in Use
If ports 8001 or 5174 are already in use:
```powershell
# Find and kill process on port 8001
Get-NetTCPConnection -LocalPort 8001 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Find and kill process on port 5174
Get-NetTCPConnection -LocalPort 5174 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Test Database Issues
Delete and recreate:
```powershell
Remove-Item backend\test_db.sqlite3
.\run-e2e-tests.ps1
```

### Script Permissions
If script won't run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## CI/CD Integration

The test script returns exit codes:
- `0` = All tests passed
- `1` = Tests failed or error occurred

Use in CI:
```yaml
- name: Run E2E Tests
  run: .\run-e2e-tests.ps1
  shell: powershell
```

## Benefits

✅ **No Pollution** - Development database stays clean  
✅ **Parallel Development** - Dev and test servers can run simultaneously  
✅ **Consistent Testing** - Fresh environment every time  
✅ **Easy Debugging** - Test videos show exactly what happened  
✅ **CI-Ready** - Automated setup and teardown  

## Development vs Test

| Aspect | Development | Test |
|--------|-------------|------|
| Database | `db.sqlite3` | `test_db.sqlite3` |
| Backend Port | 8000 | 8001 |
| Frontend Port | 5173 | 5174 |
| Settings | `settings.py` | `settings_test.py` |
| Data | Persistent | Fresh per run |

---

**Happy Testing!** 🎉

