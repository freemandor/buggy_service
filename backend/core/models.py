from django.contrib.auth.models import AbstractUser
from django.db import models
import secrets


class User(AbstractUser):
    class Role(models.TextChoices):
        DRIVER = "DRIVER", "Driver"
        DISPATCHER = "DISPATCHER", "Dispatcher"
        MANAGER = "MANAGER", "Manager"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DISPATCHER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class POI(models.Model):
    code = models.CharField(max_length=50, unique=True)  # "RECEPTION", "BEACH_BAR"
    name = models.CharField(max_length=100)              # "Reception", "Beach Bar"

    def __str__(self):
        return f"{self.code} ({self.name})"


class PoiEdge(models.Model):
    from_poi = models.ForeignKey(POI, on_delete=models.CASCADE, related_name="edges_from")
    to_poi = models.ForeignKey(POI, on_delete=models.CASCADE, related_name="edges_to")
    travel_time_s = models.PositiveIntegerField()  # seconds between these two POIs

    class Meta:
        unique_together = [("from_poi", "to_poi")]

    def save(self, *args, **kwargs):
        # enforce canonical ordering so we store each undirected pair only once
        if self.from_poi_id and self.to_poi_id and self.from_poi_id > self.to_poi_id:
            self.from_poi, self.to_poi = self.to_poi, self.from_poi
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.from_poi.code} <-> {self.to_poi.code} ({self.travel_time_s}s)"


class Buggy(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    code = models.CharField(max_length=50, unique=True)      # internal ID
    display_name = models.CharField(max_length=100)          # "Buggy #1"
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INACTIVE)

    current_poi = models.ForeignKey(POI, null=True, blank=True, on_delete=models.SET_NULL)
    current_onboard_guests = models.PositiveIntegerField(default=0)

    driver = models.OneToOneField(
        "core.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_buggy",
    )

    def __str__(self):
        return self.display_name


class RideRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ASSIGNED = "ASSIGNED", "Assigned"
        PICKING_UP = "PICKING_UP", "Picking up"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    public_code = models.CharField(max_length=12, unique=True)
    pickup_poi = models.ForeignKey(POI, on_delete=models.PROTECT, related_name="pickup_rides")
    dropoff_poi = models.ForeignKey(POI, on_delete=models.PROTECT, related_name="dropoff_rides")
    num_guests = models.PositiveIntegerField()

    room_number = models.CharField(max_length=20, blank=True)
    guest_name = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    assigned_buggy = models.ForeignKey(
        Buggy, null=True, blank=True, on_delete=models.SET_NULL, related_name="rides"
    )

    requested_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    pickup_completed_at = models.DateTimeField(null=True, blank=True)
    dropoff_completed_at = models.DateTimeField(null=True, blank=True)

    def assign_public_code(self):
        if not self.public_code:
            self.public_code = secrets.token_hex(3).upper()

    def save(self, *args, **kwargs):
        self.assign_public_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.public_code}: {self.pickup_poi} → {self.dropoff_poi}"


class BuggyRouteStop(models.Model):
    class StopType(models.TextChoices):
        PICKUP = "PICKUP", "Pickup"
        DROPOFF = "DROPOFF", "Dropoff"

    class StopStatus(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        ON_ROUTE = "ON_ROUTE", "On route"
        COMPLETED = "COMPLETED", "Completed"

    buggy = models.ForeignKey(Buggy, on_delete=models.CASCADE, related_name="route_stops")
    ride_request = models.ForeignKey(RideRequest, on_delete=models.CASCADE, related_name="route_stops")
    stop_type = models.CharField(max_length=10, choices=StopType.choices)
    status = models.CharField(max_length=15, choices=StopStatus.choices, default=StopStatus.PLANNED)

    poi = models.ForeignKey(POI, on_delete=models.PROTECT)
    sequence_index = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sequence_index"]
        unique_together = [("buggy", "sequence_index")]

    def __str__(self):
        return f"{self.buggy.display_name} [{self.sequence_index}] {self.stop_type} @ {self.poi.code}"
