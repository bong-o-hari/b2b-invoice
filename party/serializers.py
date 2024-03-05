from rest_framework.serializers import ModelSerializer
from .models import PartyDetails

class PartyShortDetailSerializer(ModelSerializer):
    class Meta:
        model = PartyDetails
        fields = ['id', 'name', 'gstin']


class PartyDetailSerializer(ModelSerializer):
    class Meta:
        model = PartyDetails
        fields = ['id', 'name', 'gstin', 'state', 'state_code', 'city', 'pincode', 'address', 'country', 'dl', 'phone']