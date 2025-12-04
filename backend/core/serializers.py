from rest_framework import serializers
from core.models import POI, Buggy, BuggyRouteStop, RideRequest, User


class POISerializer(serializers.ModelSerializer):
    class Meta:
        model = POI
        fields = ["id", "code", "name"]


class BuggySummarySerializer(serializers.ModelSerializer):
    current_poi = POISerializer()

    class Meta:
        model = Buggy
        fields = [
            "id",
            "code",
            "display_name",
            "capacity",
            "status",
            "current_poi",
            "current_onboard_guests",
        ]


class BuggyRouteStopSerializer(serializers.ModelSerializer):
    poi = POISerializer()
    ride_request_code = serializers.CharField(source="ride_request.public_code")
    num_guests = serializers.IntegerField(source="ride_request.num_guests")

    class Meta:
        model = BuggyRouteStop
        fields = [
            "id",
            "stop_type",
            "status",
            "sequence_index",
            "poi",
            "ride_request_code",
            "num_guests",
        ]


class RideRequestSerializer(serializers.ModelSerializer):
    pickup_poi = POISerializer()
    dropoff_poi = POISerializer()
    assigned_buggy = BuggySummarySerializer()

    class Meta:
        model = RideRequest
        fields = [
            "id",
            "public_code",
            "pickup_poi",
            "dropoff_poi",
            "num_guests",
            "room_number",
            "guest_name",
            "status",
            "assigned_buggy",
            "requested_at",
            "assigned_at",
            "pickup_completed_at",
            "dropoff_completed_at",
        ]


class RideRequestCreateSerializer(serializers.ModelSerializer):
    pickup_poi_code = serializers.CharField(write_only=True)
    dropoff_poi_code = serializers.CharField(write_only=True)

    class Meta:
        model = RideRequest
        fields = [
            "pickup_poi_code",
            "dropoff_poi_code",
            "num_guests",
            "room_number",
            "guest_name",
        ]

    def validate(self, attrs):
        if attrs["num_guests"] <= 0:
            raise serializers.ValidationError("num_guests must be positive")
        return attrs

    def create(self, validated_data):
        from core.models import POI
        pickup_code = validated_data.pop("pickup_poi_code")
        dropoff_code = validated_data.pop("dropoff_poi_code")

        pickup = POI.objects.get(code=pickup_code)
        dropoff = POI.objects.get(code=dropoff_code)

        ride = RideRequest.objects.create(
            pickup_poi=pickup,
            dropoff_poi=dropoff,
            **validated_data,
        )
        return ride


class RideWithAssignmentSerializer(serializers.Serializer):
    ride = RideRequestSerializer()
    assigned_buggy = BuggySummarySerializer()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "role"]

