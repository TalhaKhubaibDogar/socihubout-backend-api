from rest_framework import permissions
from events.models import Event


class IsEventOwner(permissions.BasePermission):
    message = "Event owner can view only"

    def has_permission(self, request, view):
        event_id = view.kwargs.get('id')
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return False
        return event.host == request.user


class IsWalletOwner(permissions.BasePermission):
    message = "Wallet owner can withdraw"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        wallet_id = view.kwargs.get('wallet_id')
        if wallet_id:
            return request.user.wallet.id == int(wallet_id)
        return True

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
