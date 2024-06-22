from django.urls import path
from events.api.views import (
     EventsView,
     EventsFeedView,
     JoinEventView,
     EventAttendeeView,
     TransactionListView,
     WalletView,
     WithdrawalView
)

app_name = 'events_api_v1'
urlpatterns = [
    path('user/events/', EventsView.as_view(), name="events-add-get"),
    path('user/events/<int:id>/', EventsView.as_view(), name="events-by-id"),
    path('feed/', EventsFeedView.as_view(), name="user-events-feed"),
    path('user/events/<int:event_id>/join',
         JoinEventView.as_view(), name="user-event-join"),
    path('user/events/<int:id>/attendees/',
         EventAttendeeView.as_view(), name="get-event-attendees"),
    path('transactions/', TransactionListView.as_view(), name='get-user-transaction'),
    path('wallet/', WalletView.as_view(), name='get-user-wallet'),
    path('withdrawal/', WithdrawalView.as_view(), name='withdrawal'),
]
