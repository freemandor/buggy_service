# core/services/routing.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List

from django.utils import timezone

from core.models import Buggy, BuggyRouteStop, RideRequest, POI
from core.services.graph import get_travel_time_s

PICKUP_SERVICE_S = 25
DROPOFF_SERVICE_S = 25


@dataclass
class SimulatedStop:
    ride_request: RideRequest
    stop_type: str  # "PICKUP" or "DROPOFF"
    poi: POI
    num_guests: int


@dataclass
class SimResult:
    pickup_time_s: int
    total_time_s: int


class NoActiveBuggiesError(Exception):
    pass


def build_current_route_for_buggy(buggy: Buggy) -> List[SimulatedStop]:
    stops = (
        BuggyRouteStop.objects
        .filter(buggy=buggy)
        .exclude(status=BuggyRouteStop.StopStatus.COMPLETED)
        .order_by("sequence_index")
        .select_related("ride_request", "poi")
    )
    sim_stops: List[SimulatedStop] = []
    for s in stops:
        sim_stops.append(
            SimulatedStop(
                ride_request=s.ride_request,
                stop_type=s.stop_type,
                poi=s.poi,
                num_guests=s.ride_request.num_guests,
            )
        )
    return sim_stops


def simulate_append_for_buggy(*, buggy: Buggy, current_route: List[SimulatedStop], new_ride: RideRequest) -> SimResult:
    time_s = 0
    current_poi = buggy.current_poi or new_ride.pickup_poi
    onboard = buggy.current_onboard_guests

    # existing route
    for stop in current_route:
        time_s += get_travel_time_s(current_poi, stop.poi)
        current_poi = stop.poi

        if stop.stop_type == BuggyRouteStop.StopType.PICKUP:
            time_s += PICKUP_SERVICE_S
            onboard += stop.num_guests
        else:
            time_s += DROPOFF_SERVICE_S
            onboard -= stop.num_guests

    # new pickup
    time_s += get_travel_time_s(current_poi, new_ride.pickup_poi)
    pickup_time_s = time_s
    time_s += PICKUP_SERVICE_S
    onboard += new_ride.num_guests

    # new dropoff
    time_s += get_travel_time_s(new_ride.pickup_poi, new_ride.dropoff_poi)
    time_s += DROPOFF_SERVICE_S
    onboard -= new_ride.num_guests

    return SimResult(pickup_time_s=pickup_time_s, total_time_s=time_s)


def append_stops_for_buggy(buggy: Buggy, new_ride: RideRequest) -> None:
    last_stop = (
        BuggyRouteStop.objects.filter(buggy=buggy)
        .order_by("-sequence_index")
        .first()
    )
    start_index = last_stop.sequence_index + 1 if last_stop else 0

    BuggyRouteStop.objects.create(
        buggy=buggy,
        ride_request=new_ride,
        stop_type=BuggyRouteStop.StopType.PICKUP,
        poi=new_ride.pickup_poi,
        sequence_index=start_index,
        status=BuggyRouteStop.StopStatus.PLANNED,
    )

    BuggyRouteStop.objects.create(
        buggy=buggy,
        ride_request=new_ride,
        stop_type=BuggyRouteStop.StopType.DROPOFF,
        poi=new_ride.dropoff_poi,
        sequence_index=start_index + 1,
        status=BuggyRouteStop.StopStatus.PLANNED,
    )


def assign_ride_to_best_buggy(new_ride: RideRequest) -> Buggy:
    active_buggies = Buggy.objects.filter(status=Buggy.Status.ACTIVE)

    if not active_buggies.exists():
        raise NoActiveBuggiesError("No active buggies available")

    best_buggy = None
    best_sim = None

    for buggy in active_buggies:
        current_route = build_current_route_for_buggy(buggy)
        sim = simulate_append_for_buggy(buggy=buggy, current_route=current_route, new_ride=new_ride)

        if best_sim is None or sim.pickup_time_s < best_sim.pickup_time_s:
            best_sim = sim
            best_buggy = buggy

    append_stops_for_buggy(best_buggy, new_ride)
    new_ride.assigned_buggy = best_buggy
    new_ride.status = RideRequest.Status.ASSIGNED
    new_ride.assigned_at = timezone.now()
    new_ride.save(update_fields=["assigned_buggy", "status", "assigned_at"])
    return best_buggy

