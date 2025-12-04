from django.urls import path
from core import views

urlpatterns = [
    path("auth/me/", views.MeView.as_view()),
    path("buggies/", views.BuggiesListView.as_view()),
    path("rides/", views.RidesListView.as_view()),
    path("rides/create-and-assign/", views.RideCreateAndAssignView.as_view()),
    path("driver/my-route/", views.DriverMyRouteView.as_view()),
    path("driver/stops/<int:stop_id>/start/", views.DriverStopStartView.as_view()),
    path("driver/stops/<int:stop_id>/complete/", views.DriverStopCompleteView.as_view()),
    path("metrics/summary/", views.MetricsSummaryView.as_view()),
]

