from rest_framework import serializers
from core.models import POI, PoiEdge, Buggy, BuggyRouteStop, RideRequest, User


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


# Manager CRUD Serializers

class BuggyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating buggies."""
    driver_id = serializers.IntegerField(required=False, allow_null=True)
    current_poi_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Buggy
        fields = [
            "id",
            "code",
            "display_name",
            "capacity",
            "status",
            "driver_id",
            "current_poi_id",
            "current_onboard_guests",
        ]
        read_only_fields = ["id"]
    
    def validate_driver_id(self, value):
        if value is not None:
            if not User.objects.filter(id=value, role=User.Role.DRIVER).exists():
                raise serializers.ValidationError("Driver not found or user is not a driver")
        return value
    
    def validate_current_poi_id(self, value):
        if value is not None:
            if not POI.objects.filter(id=value).exists():
                raise serializers.ValidationError("POI not found")
        return value
    
    def create(self, validated_data):
        driver_id = validated_data.pop('driver_id', None)
        current_poi_id = validated_data.pop('current_poi_id', None)
        
        if driver_id:
            validated_data['driver_id'] = driver_id
        if current_poi_id:
            validated_data['current_poi_id'] = current_poi_id
            
        return Buggy.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        driver_id = validated_data.pop('driver_id', None)
        current_poi_id = validated_data.pop('current_poi_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if driver_id is not None:
            instance.driver_id = driver_id
        if current_poi_id is not None:
            instance.current_poi_id = current_poi_id
            
        instance.save()
        return instance


class DriverCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating drivers."""
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ["id", "username", "password", "first_name", "last_name", "role"]
        read_only_fields = ["id", "role"]
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({"password": "This field is required."})
        user = User.objects.create(
            role=User.Role.DRIVER,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class POICreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating POIs."""
    
    class Meta:
        model = POI
        fields = ["id", "code", "name"]
        read_only_fields = ["id"]
    
    def validate_code(self, value):
        # Ensure code is uppercase
        return value.upper()


class POIEdgeSerializer(serializers.ModelSerializer):
    """Serializer for viewing POI edges with full POI details."""
    from_poi = POISerializer(read_only=True)
    to_poi = POISerializer(read_only=True)
    
    class Meta:
        model = PoiEdge
        fields = ["id", "from_poi", "to_poi", "travel_time_s"]
        read_only_fields = ["id"]


class POIEdgeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating POI edges."""
    from_poi_id = serializers.IntegerField(required=False)
    to_poi_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = PoiEdge
        fields = ["id", "from_poi_id", "to_poi_id", "travel_time_s"]
        read_only_fields = ["id"]
    
    def validate_from_poi_id(self, value):
        if not POI.objects.filter(id=value).exists():
            raise serializers.ValidationError("From POI not found")
        return value
    
    def validate_to_poi_id(self, value):
        if not POI.objects.filter(id=value).exists():
            raise serializers.ValidationError("To POI not found")
        return value
    
    def validate(self, data):
        # For create operations, ensure both POIs are provided
        if not self.instance:
            if 'from_poi_id' not in data or 'to_poi_id' not in data:
                raise serializers.ValidationError("Both from_poi_id and to_poi_id are required")
        
        # Prevent self-loops
        from_poi_id = data.get('from_poi_id')
        to_poi_id = data.get('to_poi_id')
        
        # If updating and only one POI is provided, use the existing one
        if self.instance:
            if from_poi_id is None:
                from_poi_id = self.instance.from_poi_id
            if to_poi_id is None:
                to_poi_id = self.instance.to_poi_id
        
        if from_poi_id == to_poi_id:
            raise serializers.ValidationError("Cannot create edge from POI to itself")
        
        return data
    
    def create(self, validated_data):
        from_poi_id = validated_data.pop('from_poi_id')
        to_poi_id = validated_data.pop('to_poi_id')
        
        edge = PoiEdge.objects.create(
            from_poi_id=from_poi_id,
            to_poi_id=to_poi_id,
            **validated_data
        )
        return edge
    
    def update(self, instance, validated_data):
        from_poi_id = validated_data.pop('from_poi_id', None)
        to_poi_id = validated_data.pop('to_poi_id', None)
        
        if from_poi_id is not None:
            instance.from_poi_id = from_poi_id
        if to_poi_id is not None:
            instance.to_poi_id = to_poi_id
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

