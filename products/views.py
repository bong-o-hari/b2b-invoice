import io
import csv
from djqscsv import render_to_csv_response
from inboicing_system.pagination import StandardResultsSetPagination
from inboicing_system.settings import logger
from inboicing_system.core.permissions import IsWarehouseOperator
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import *

# Create your views here.

@csrf_exempt
@api_view(['GET'])
def get_products_csv(request):
    products = ProductMaster.objects.filter(is_deleted=False).values('product_name', 'mrp', 'hsn_code', 'gst_percent', 'primary_box_qty', 'pack')
    return render_to_csv_response(products)


@csrf_exempt
@api_view(['GET'])
def get_product_list(request, name):
    products = ProductMaster.objects.filter(product_name__icontains=name).all()
    serializer = ProductShortDetailSerializer(products, many=True)
    return Response({"success": True, "choices": serializer.data}, status=status.HTTP_200_OK)


class ProductInvoiceSelectionView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    serializer_class = ProductShortDetailSerializer

    def get_queryset(self):
        logger.info("PRODUCT DASHBOARD VIEW: filtering product data!")
        products = ProductMaster.objects.filter(is_deleted=False).order_by('-created_at').all()
        return products


class ProductCreationView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        data = request.data
        try:
            serializer = ProductDetailSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            product_master = serializer.save()

            logger.info(f"PRODUCT CREATION VIEW: Successfully created product object PRODUCT: {product_master.id}")
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"PRODUCT CREATION VIEW: Something went wrong while creating product object DATA: {data} ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        from .utils import get_product_from_id
        data = request.data
        try:
            product = get_product_from_id(product_id=data.pop('id', None))
            serializer = ProductDetailSerializer(instance=product, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            product_details = serializer.save()
            
            logger.error(f"PRODUCT UPDATE VIEW: Successfully updated product object PRODUCT: {product_details.id}")
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"PRODUCT UPDATE VIEW: Something went wrong while updating product object DATA: {data} ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductInvoiceCompletionView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, product_id):
        from .utils import get_product_from_id
        try:
            product = get_product_from_id(product_id=product_id)
            serializer = ProductDetailSerializer(product)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"GET PRODUCT BY ID: Something went wrong while getting product details! PRODUCT: {product_id} ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductBulkUploadView(APIView):
    """
    View to Create invoices from csv uploads
    """
    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        try:
            product_csv = request.FILES['product_csv'].read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(product_csv))
        except Exception as err:
            logger.error(f"PRODUCT BULK UPLOAD: CSV reading error! ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_data = [ line for line in csv_reader ]

            logger.info(f"PRODUCT BULK UPLOAD: Length of CSV entries {len(product_data)}")

            for data in product_data:
                logger.info(f"PRODUCT BULK LOOP: Loop data {data}")
                serializer = ProductDetailSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return Response({"success": True, "message": "Products added successfully!"}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"PRODUCT BULK UPLOAD: Loop broke! ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_400_BAD_REQUEST)