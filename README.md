# Club Med Seychelles - Buggy Service

A complete monorepo implementation with Django backend (graph-based routing) and React TypeScript frontend.

## System Status

✅ **Backend:** Running on http://localhost:8000
✅ **Frontend:** Running on http://localhost:5173

## Quick Start

### Backend (Already Running)
The Django backend is running in terminal 5 on port 8000.

### Frontend (Already Running)
The Vite dev server is running in terminal 9 on port 5173.

## Test Accounts

- **Dispatcher:** `dispatcher` / `dispatcher`
- **Driver:** `driver1` / `driver1`
- **Manager:** `manager` / `manager`

## Pre-Seeded Data

- **POIs:** Reception, Beach Bar, Bel Air
- **Edges:** 
  - Bel Air ↔ Beach Bar: 120s
  - Reception ↔ Beach Bar: 240s  
  - Reception ↔ Bel Air: 90s
- **Buggy #1:** Active at Bel Air, assigned to driver1

## Testing the System

### 1. Test Dispatcher Dashboard
1. Open http://localhost:5173
2. Login as `dispatcher` / `dispatcher`
3. Create a new ride:
   - Pickup: RECEPTION
   - Dropoff: BEACH_BAR
   - Guests: 2
   - Room: 101
   - Name: Test Guest
4. Verify ride is assigned to Buggy #1
5. Check the buggies and rides tables update

### 2. Test Driver Interface
1. Logout and login as `driver1` / `driver1`
2. View your route stops
3. Click "Start" on the first stop
4. Click "Complete" after it changes to ON_ROUTE
5. Continue through all stops

### 3. Test Manager Dashboard
1. Logout and login as `manager` / `manager`
2. View today's metrics (total rides, average wait time)
3. See buggy status overview
4. Check recent rides list

## Architecture

### Backend (`/backend`)
- **Django 5.2.9** with Python 3.14
- **DRF + JWT** authentication
- **Graph-based routing** with Dijkstra's algorithm
- **SQLite** database
- **Unit tests** for graph and routing logic

### Frontend (`/frontend`)
- **React 18** with TypeScript
- **Vite** for fast development
- **React Router** for navigation
- **Role-based** dashboards (Dispatcher, Driver, Manager)

## Key Features Implemented

- ✅ User authentication with JWT
- ✅ Role-based access control (DRIVER, DISPATCHER, MANAGER)
- ✅ Graph-based POI routing with shortest path calculation
- ✅ Intelligent ride assignment (picks buggy with earliest pickup time)
- ✅ Real-time buggy location and guest tracking
- ✅ Driver route management (start/complete stops)
- ✅ Dispatcher ride creation and monitoring
- ✅ Manager analytics dashboard
- ✅ Comprehensive unit tests

## API Endpoints

- `POST /api/auth/login/` - Login and get JWT token
- `GET /api/auth/me/` - Get current user info
- `GET /api/buggies/` - List all buggies
- `GET /api/rides/` - List recent rides
- `POST /api/rides/create-and-assign/` - Create and auto-assign ride
- `GET /api/driver/my-route/` - Get driver's route stops
- `POST /api/driver/stops/{id}/start/` - Start a stop
- `POST /api/driver/stops/{id}/complete/` - Complete a stop
- `GET /api/metrics/summary/` - Get daily metrics

## Development Commands

### Backend
```bash
cd backend
.venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Run Tests
```bash
cd backend
.venv\Scripts\python.exe manage.py test
```

## Project Structure

```
buggy_service/
├── backend/
│   ├── buggy_project/      # Django settings
│   ├── core/               # Main app
│   │   ├── models.py       # Database models
│   │   ├── views.py        # API views
│   │   ├── serializers.py  # DRF serializers
│   │   ├── services/       # Business logic
│   │   │   ├── graph.py    # Dijkstra pathfinding
│   │   │   └── routing.py  # Ride assignment
│   │   ├── tests/          # Unit tests
│   │   └── management/     # Management commands
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── api/            # API client layer
│   │   ├── auth/           # Auth context & routing
│   │   ├── components/     # Reusable components
│   │   └── pages/          # Page components
│   └── package.json
└── README.md
```

## Next Steps (Future Enhancements)

- Add WebSocket support for real-time updates
- Implement capacity checking (buggy full prevention)
- Add route optimization with multiple pickups
- Create guest-facing booking interface
- Add historical analytics and reporting
- Deploy to production environment

---

Built with ❤️ for Club Med Seychelles

