import io
import csv
from djqscsv import render_to_csv_response
from inboicing_system.pagination import StandardResultsSetPagination
from inboicing_system.settings import logger
from inboicing_system.core.permissions import IsWarehouseOperator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import PartyShortDetailSerializer, PartyDetailSerializer
from .models import PartyDetails
# Create your views here.

@csrf_exempt
@api_view(['GET'])
def get_parties_csv(request):
    parties = PartyDetails.objects.filter(is_deleted=False).values('name', 'gstin', 'dl', 'phone', 'address', 'city', 'state', 'pincode', 'state_code', 'country')
    return render_to_csv_response(parties)


@csrf_exempt
@api_view(['GET'])
def get_parties_list(request, search_str):
    parties = PartyDetails.objects.filter(Q(gstin__icontains=search_str) | Q(name__icontains=search_str)).all()
    serializer = PartyDetailSerializer(parties, many=True)
    return Response({"success": True, "choices": serializer.data}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
def get_state_code_list(request):
    from .choices import StateCodes
    state_codes = {}
    for value, label in StateCodes.choices:
        state_codes[label] = value
    return Response({"success": True, "choices": state_codes}, status=status.HTTP_200_OK)


class PartyInvoiceSelectionView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardResultsSetPagination
    serializer_class = PartyShortDetailSerializer

    def get_queryset(self):
        logger.info("PARTY DASHBOARD VIEW: filtering party data!")
        parties = PartyDetails.objects.filter(is_deleted=False).order_by('-created_at').all()
        return parties


class PartyCreationView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        data = request.data
        try:
            serializer = PartyDetailSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            party_details = serializer.save()

            logger.error(f"PARTY CREATION VIEW: Successfully created party object PARTY: {party_details.id}")
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"PARTY CREATION VIEW: Something went wrong while creating party object DATA: {data} ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        from .utils import get_party_by_id
        data = request.data
        try:
            party = get_party_by_id(party_id=data.pop('id', None))
            serializer = PartyDetailSerializer(instance=party, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            party_details = serializer.save()
            
            logger.error(f"PARTY UPDATE VIEW: Successfully updated party object PARTY: {party_details.id}")
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"PARTY UPDATE VIEW: Something went wrong while updating party object DATA: {data} ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PartyInvoiceCompletionView(APIView):

    def get(self, request, party_id):
        from .utils import get_party_by_id
        try:
            party = get_party_by_id(party_id=party_id)
            serializer = PartyDetailSerializer(party)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"GET PARTY BY ID: Something went wrong while getting party details! PARTY: {party_id} ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PartyBulkUploadView(APIView):
    """
    View to Create invoices from csv uploads
    """
    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        try:
            party_csv = request.FILES['party_csv'].read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(party_csv))
        except Exception as err:
            logger.error(f"PARTY BULK UPLOAD: CSV reading error! ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            party_data = [ line for line in csv_reader ]

            logger.info(f"PARTY BULK UPLOAD: Length of CSV entries {len(party_data)}")

            for data in party_data:
                logger.info(f"PARTY BULK LOOP: Loop data {data}")
                serializer = PartyDetailSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                

            return Response({"success": True, "message": "Tasks scheduled successfully!"}, status=status.HTTP_200_OK)
        except Exception as err:
            logger.error(f"PARTY BULK UPLOAD: Loop broke! ERROR: {str(err)}")
            return Response({"success": False, "message": str(err)}, status=status.HTTP_400_BAD_REQUEST)