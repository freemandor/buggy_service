from django.urls import path
from core import views

urlpatterns = [
    path("auth/me/", views.MeView.as_view()),
    path("pois/", views.POIsListView.as_view()),
    path("buggies/", views.BuggiesListView.as_view()),
    path("rides/", views.RidesListView.as_view()),
    path("rides/create-and-assign/", views.RideCreateAndAssignView.as_view(), name="rides-create-and-assign"),
    path("driver/my-route/", views.DriverMyRouteView.as_view()),
    path("driver/stops/<int:stop_id>/start/", views.DriverStopStartView.as_view(), name="driver-stop-start"),
    path("driver/stops/<int:stop_id>/complete/", views.DriverStopCompleteView.as_view(), name="driver-stop-complete"),
    path("driver/ride-notifications/", views.DriverRideNotificationsView.as_view(), name="driver-ride-notifications"),
    
    # Dispatcher SSE
    path("dispatcher/ride-notifications/", views.DispatcherRideNotificationsView.as_view(), name="dispatcher-ride-notifications"),
    path("metrics/summary/", views.MetricsSummaryView.as_view()),
    
    # Manager CRUD endpoints
    path("manager/buggies/", views.BuggyCRUDView.as_view(), name="manager-buggy-list"),
    path("manager/buggies/<int:buggy_id>/", views.BuggyCRUDView.as_view(), name="manager-buggy-detail"),
    path("manager/drivers/", views.DriverCRUDView.as_view(), name="manager-driver-list"),
    path("manager/drivers/<int:driver_id>/", views.DriverCRUDView.as_view(), name="manager-driver-detail"),
    path("manager/pois/", views.POICRUDView.as_view(), name="manager-poi-list"),
    path("manager/pois/<int:poi_id>/", views.POICRUDView.as_view(), name="manager-poi-detail"),
    path("manager/poi-edges/", views.POIEdgeCRUDView.as_view(), name="manager-poi-edge-list"),
    path("manager/poi-edges/<int:edge_id>/", views.POIEdgeCRUDView.as_view(), name="manager-poi-edge-detail"),
]

