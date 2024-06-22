from rest_framework.status import (
    HTTP_200_OK as RES_200,
    HTTP_201_CREATED as RES_201,
    HTTP_202_ACCEPTED as RES_202,
    HTTP_400_BAD_REQUEST as RES_400,
    HTTP_401_UNAUTHORIZED as RES_401,
    HTTP_403_FORBIDDEN as RES_403,
    HTTP_404_NOT_FOUND as RES_404,
    HTTP_500_INTERNAL_SERVER_ERROR as RES_500,
)
from common.messages import (
    EVENTS_RETRIEVED,
    EVENT_CREATED,
    EVENT_UNAUTHORIZED_DELETE,
    EVENT_INVALID,
    EVENT_NOT_FOUND,
    EVENT_DELETED,
    EVENT_FEED_RETRIEVED,
    EVENT_ALREADY_ENDED, 
    EVENT_NOT_STARTED,
    EVENT_ALREADY_JOINED,
    EVENT_JOINED_SUCCESS,
    USER_NO_WALLET,
    INVALID_REFERRAL_CODE,
    EVENT_ATTENDEES_RETRIEVED,
    USER_REFERRAL_BONUS_LIST,
    WALLET_DETAILS_RETRIEVED,
    MIN_WITHDRAWAL_AMOUNT,
    INSUFFICIENT_BALANCE,
    WITHDRAWAL_SUCCESS
)
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from users.models import (
    User,
    Keyword,
    UserPreference,
    Wallet
)
from events.models import (
    Event,
    EventAttendee,
    Wallet,
    Transaction
)
from events.api.serializers import(
    EventSerializer,
    EventFeedSerializer,
    EventAttendeeSerializer,
    WalletSerializer,
    TransactionSerializer

)
from events.permissions import IsEventOwner, IsWalletOwner
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError, ParseError
from users.permissions import IsHostUser, IsNormalUser
import traceback
from django.db.models import Q
from django.http import Http404
from decimal import Decimal
from django.utils import timezone
from common.utils import success_response_builder as sr
from common.utils import error_response_builder as er
# Create your views here.


class EventsView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsHostUser]
    lookup_field = 'id'

    def get_queryset(self):
        return Event.objects.filter(host=self.request.user).order_by('start_datetime')

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    def get(self, request, *args, **kwargs):
        print(kwargs)
        if "id" in kwargs:
            print("in")
            event = self.get_object()
            response = super().get(request, *args, **kwargs)
            response.data = sr(message=EVENTS_RETRIEVED, data=response.data)
            # {
            #     "status_code": status.HTTP_200_OK,
            #     "message": "Event Retrieved Successfully",
            #     "data": response.data
            # }
            return response
        else:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(sr(message=EVENTS_RETRIEVED, data=serializer.data), status=RES_200)

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return Response(sr(message=EVENT_CREATED, data=serializer.data))
            return Response(er(message=serializer.errors), status=RES_400)
        except ValidationError as e:
            return Response(er(message=e.args[0]), status=RES_400)

        except Exception as e:
            print("Exception:", str(e))
            traceback.print_exc()
            return Response(er(code=500, message=str(e)), status=RES_500)
            return Response({
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message_code": "Internal Server Error",
                "data": {
                    "message": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            event = self.get_object()
        except Http404:
            return Response(er(code=404, message=EVENT_NOT_FOUND), status=RES_404)
        try:
            if event.host != request.user:
                raise ParseError(EVENT_UNAUTHORIZED_DELETE)
            event.delete()
            return Response(sr(message=EVENT_DELETED), status=RES_200)
        except ParseError as e:
            return Response(er(message=e.args[0]), status=RES_400)


class EventsFeedView(generics.ListAPIView):
    serializer_class = EventFeedSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_queryset(self):
        user = self.request.user
        user_preferences = user.preferences.all()
        current_time = timezone.now()

        if user_preferences.exists():
            preferred_keyword_ids = user_preferences.values_list(
                'keyword__id', flat=True)
            query = Q()
            for keyword_id in preferred_keyword_ids:
                query |= Q(keywords__id=keyword_id)
            events = Event.objects.filter(
                query, end_datetime__gt=current_time).distinct().order_by('start_datetime')
            return events
        return Event.objects.none()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(
                queryset, many=True, context={'request': request})
            return Response(sr(message=EVENT_FEED_RETRIEVED, data=serializer.data), status=RES_200)
        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_400)


class JoinEventView(generics.CreateAPIView):
    serializer_class = EventAttendeeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            event_id = kwargs.get('event_id')
            referral_code = request.query_params.get('referral_code')
            user = request.user

            event = Event.objects.filter(id=event_id).first()
            if not event:
                return Response(er(message=EVENT_NOT_FOUND), status=RES_400)

            current_time = timezone.now()
            if event.end_datetime <= current_time:
                return Response(er(message=EVENT_ALREADY_ENDED), status=RES_400)
                return Response({
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message_code": "Error",
                    "data": {
                        "message": "Event has already ended"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            if event.start_datetime > current_time:
                return Response(er(message=EVENT_NOT_STARTED), status=RES_400)

            if EventAttendee.objects.filter(event_id=event_id, user=user).exists():
                return Response(er(message=EVENT_ALREADY_JOINED), status=RES_400)

            if not hasattr(user, 'wallet'):
                return Response(er(message=USER_NO_WALLET), status=RES_400)

            attendee = EventAttendee.objects.create(
                event=event, user=user, referral_code=referral_code)

            if referral_code:
                referrer = User.objects.filter(
                    referral_code=referral_code).first()
                if referrer:
                    referrer_wallet = referrer.wallet
                    referrer_wallet.balance += Decimal('0.25')
                    referrer_wallet.save()
                    Transaction.objects.create(
                        wallet=referrer_wallet, user=referrer, amount=Decimal('0.25'))
                else:
                    return Response(er(message=INVALID_REFERRAL_CODE), status=RES_400)
                    return Response({
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message_code": "Error",
                        "data": {
                            "message": "Invalid referral code"
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            return Response(sr(message=EVENT_JOINED_SUCCESS), status=RES_200)

        except Exception as e:
            return Response(er(message=e.args[0]), status=RES_400)


class EventAttendeeView(generics.ListAPIView):
    serializer_class = EventAttendeeSerializer
    permission_classes = [IsAuthenticated, IsEventOwner]

    def get_queryset(self):
        event_id = self.kwargs.get('id')
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise ParseError(detail=EVENT_NOT_FOUND)
        return EventAttendee.objects.filter(event=event)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(sr(message=EVENT_ATTENDEES_RETRIEVED, data=serializer.data), status=RES_200)
            return Response({
                "code": status.HTTP_200_OK,
                "message_code": "Event Attendees Retrieved Successfully",
                "data": {
                    "Items": serializer.data
                }
            }, status=status.HTTP_200_OK)
        except ParseError as e:
            return Response(sr(message=e.args[0]), status=RES_404)
            return Response({
                "code": status.HTTP_404_NOT_FOUND,
                "message_code": str(e),
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(sr(message=e.args[0]), status=RES_404)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message_code": "An error occurred.",
                "data": {
                    "error": str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class WalletView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_object(self):
        return self.request.user.wallet

    def get(self, request, *args, **kwargs):
        try:
            query = self.get_object()
            serializer = self.get_serializer(query)
            return Response(sr(message=WALLET_DETAILS_RETRIEVED, data=serializer.data),status=RES_200)
            return Response({
                "code": status.HTTP_200_OK,
                "message_code": "User Wallet Details",
                "data": {
                    "Items": serializer.data
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(er(message=e.args[0]),status=RES_400)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message_code": "An error occurred.",
                "data": {
                    "error": str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsNormalUser]

    def get_queryset(self):
        return self.request.user.wallet.transactions.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(sr(message=USER_REFERRAL_BONUS_LIST, data=serializer.data), status=RES_200)
        except Exception as e:
            return Response(er(message=e.args[0]),status=RES_400)


class WithdrawalView(generics.GenericAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsNormalUser, IsWalletOwner]

    def post(self, request, *args, **kwargs):
        try:
            withdrawal_amount = Decimal(request.data.get('amount', '0.00'))
            user = request.user

            if withdrawal_amount < Decimal('1.00'):
                return Response(er(message=MIN_WITHDRAWAL_AMOUNT), status=RES_400)

            wallet = user.wallet
            if wallet.balance < withdrawal_amount:
                return Response(er(message=INSUFFICIENT_BALANCE), status=RES_400)
            
            wallet.balance -= withdrawal_amount
            wallet.save()

            transaction = Transaction.objects.create(
                wallet=wallet,
                user=user,
                amount=-withdrawal_amount
            )
            return Response(sr(message=WITHDRAWAL_SUCCESS, data=TransactionSerializer(transaction).data), status=RES_200)
            return Response({
                "code": status.HTTP_201_CREATED,
                "message_code": "Withdrawal successful.",
                "data": {
                    "transaction": TransactionSerializer(transaction).data
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(er(message=e.args[0]),status=RES_400)
            return Response({
                "code": status.HTTP_400_BAD_REQUEST,
                "message_code": "An error occurred.",
                "data": {
                    "error": str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)