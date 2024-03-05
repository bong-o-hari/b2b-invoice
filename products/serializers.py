from rest_framework.serializers import ModelSerializer
from .models import *

class ProductDetailSerializer(ModelSerializer):
    class Meta:
        model = ProductMaster
        fields = '__all__'


class ProductShortDetailSerializer(ModelSerializer):
    class Meta:
        model = ProductMaster
        fields = ('id', 'product_name', 'mrp', 'hsn_code', 'gst_percent')