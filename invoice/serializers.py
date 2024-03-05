from rest_framework.serializers import ModelSerializer, DateField, ReadOnlyField

from .models import *


class InvoiceDetailSerializer(ModelSerializer):
    invoice_date = DateField(format="%Y-%m-%d")
    appointment_date = DateField(format="%Y-%m-%d")
    delivery_date = DateField(format="%Y-%m-%d")
    class Meta:
        model = InvoiceDetails
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.bill_to_party = validated_data.get('bill_to_id', instance.bill_to_party)
        instance.ship_to_party = validated_data.get('ship_to_id', instance.ship_to_party)
        instance.save()
        return instance

class InvoiceShortDetailSerializer(ModelSerializer):
    invoice_date = DateField(format="%Y-%m-%d")
    class Meta:
        model = InvoiceDetails
        fields = ('id', 'invoice_number', 'invoice_sequence', 'status', 'invoice_date')


class InvoiceProductsDetailSerializer(ModelSerializer):
    from products.serializers import ProductShortDetailSerializer
    
    expiry = DateField(format="%Y-%m-%d")
    po_date = DateField(format="%Y-%m-%d")
    product = ProductShortDetailSerializer()
    class Meta:
        model = InvoiceProductDetails
        exclude = ('invoice',)


class InvoiceExpandedDetailSerializer(ModelSerializer):
    from party.serializers import PartyDetailSerializer

    seller = PartyDetailSerializer()
    bill_to_party = PartyDetailSerializer()
    ship_to_party = PartyDetailSerializer()
    products = ReadOnlyField()
    invoice_pdf_url = ReadOnlyField(source='complete_invoice_url')
    box_label_url = ReadOnlyField(source='complete_box_label_url')
    e_invoice_url = ReadOnlyField(source='complete_e_invoice_url')
    eway_bill = ReadOnlyField(source='complete_ewaybill_url')
    
    class Meta:
        model = InvoiceDetails
        fields = '__all__'
