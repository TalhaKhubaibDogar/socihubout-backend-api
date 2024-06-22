from common.messages import(
    REQUEST_BODY_EMPTY,
    EVENT_ADDRESS_REQUIRED,
    EVENT_NAME_REQUIRED,
    EVENT_LATITUDE_REQUIRED,
    EVENT_LOCATION_URL_REQUIRED,
    EVENT_KEYWORDS_REQUIRED,
    EVENT_DESCRIPTION_REQUIRED,
    EVENT_LONGITUDE_REQUIRED,
    EVENT_START_DATE_REQUIRED,
    EVENT_END_DATE_REQUIRED,
    EVENT_START_DATE_FUTURE,
    EVENT_END_DATE_AFTER_START
)
from users.models import(
    Keyword,
    UserPreference,
    User,
    Wallet
)
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError
from django.utils import timezone
from common.utils import success_response_builder as sr
from common.utils import error_response_builder as er
from events.models import (
    Event,
    EventAttendee,
    Transaction
)

class EventSerializer(serializers.ModelSerializer):
    keywords = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )

    class Meta:
        model = Event
        fields = ['id', 'name', 'location_url', 'address',
                  'latitude', 'longitude', 'keywords', 'host', 'start_datetime', 'end_datetime', 'description']
        read_only_fields = ['host']

    def create(self, validated_data):
        keyword_names = validated_data.pop('keywords', [])
        event = Event.objects.create(**validated_data)
        for keyword_name in keyword_names:
            keyword, _ = Keyword.objects.get_or_create(
                name=keyword_name)
            event.keywords.add(keyword)
        return event

    def validate(self, data):
        if not data:
            raise serializers.ValidationError(REQUEST_BODY_EMPTY)
        if not data.get('name'):
            raise serializers.ValidationError(EVENT_NAME_REQUIRED)
        if not data.get('location_url'):
            raise serializers.ValidationError(EVENT_LOCATION_URL_REQUIRED)
        if not data.get('address'):
            raise serializers.ValidationError(EVENT_ADDRESS_REQUIRED)
        if not data.get('latitude'):
            raise serializers.ValidationError(EVENT_LATITUDE_REQUIRED)
        if not data.get('longitude'):
            raise serializers.ValidationError(EVENT_LONGITUDE_REQUIRED)
        if not data.get('start_datetime'):
            raise serializers.ValidationError(EVENT_START_DATE_REQUIRED)
        if not data.get('end_datetime'):
            raise serializers.ValidationError(EVENT_END_DATE_REQUIRED)
        if not data.get('keywords'):
            raise serializers.ValidationError(EVENT_KEYWORDS_REQUIRED)
        if not data.get('description'):
            raise serializers.ValidationError(EVENT_DESCRIPTION_REQUIRED)

        current_time = timezone.now()
        start_datetime = data['start_datetime']
        end_datetime = data['end_datetime']

        if start_datetime <= current_time:
            raise ParseError(EVENT_START_DATE_FUTURE)
        if end_datetime <= start_datetime:
            raise ParseError(EVENT_END_DATE_AFTER_START)

        return data


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')


class EventFeedSerializer(serializers.ModelSerializer):
    host_details = UserSerializer(source='host', read_only=True)
    is_joined = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'name', 'location_url', 'address',
                  'latitude', 'longitude', 'keywords', 'host', 'start_datetime', 'end_datetime', 'host_details', 'is_joined', 'description']
        read_only_fields = ['host']

    def get_is_joined(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return EventAttendee.objects.filter(event=obj, user=request.user).exists()
        return False


class EventAttendeeSerializer(serializers.ModelSerializer):
    event_details = EventFeedSerializer(source='event', read_only=True)
    attendee_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = EventAttendee
        fields = ['event', 'user', 'event_joined_at', 'created_at',
                  'updated_at', 'event_details', 'attendee_details', 'referral_code']
        read_only_fields = ['event_joined_at', 'created_at', 'updated_at']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance']


class TransactionSerializer(serializers.ModelSerializer):
    wallet_details = WalletSerializer(source='wallet', read_only=True)
    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'wallet', 'user', 'amount', 'created_at',
                  'wallet_details', 'user_details']
        read_only_fields = ['id', 'wallet', 'user',
                            'created_at', 'wallet_details', 'user_details']
