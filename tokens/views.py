from datetime import date
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from tokens.models import Counter, Department, Tokens
from utils.send_message_socket import send_token_display_update

# Create your views here.

class CreateTokensAPI(APIView):
    # throttle_classes = [CustomThrottle]

    class InputSerializer(serializers.Serializer):
        department = serializers.IntegerField(required=True)
        counter = serializers.IntegerField(required=False, allow_null=True)
        description = serializers.CharField(required=False, allow_blank=True)
        priority = serializers.IntegerField(required=False, allow_null=True)
        service = serializers.IntegerField(required=False, allow_null=True)
        token_no = serializers.IntegerField(required=False, allow_null=True)
        token_created_for = serializers.DateField(required=False, allow_null=True)
        schedule_list = serializers.IntegerField(required=False, allow_null=True)
        patient = serializers.IntegerField(required=False, allow_null=True)
    
    def post(self, request, *args, **kwargs):
        today = date.today()
        try:
            request_data = request.data
            input_serializer = self.InputSerializer(data=request_data)
            if not input_serializer.is_valid():
                return Response(data=input_serializer.errors, message="Invalid Data")

            department_id = input_serializer.validated_data.get("department")
            counter_id = input_serializer.validated_data.get("counter")

            department = Department.objects.filter(id=department_id).defer('created_at','updated_at','created_by_id','updated_by_id').order_by("-id").first()
            if not department:
                return Response(message="No Department Found for the ID provided")

            counter = None
            counter_wise_token = department.is_counter_queue_node

            if counter_wise_token and counter_id is None:
                return Response(message="Counter ID is required for this department")

            if counter_id:
                counter = Counter.objects.filter(id=counter_id).select_related("department").order_by("-id").first()
                if not counter:
                    return Response(message="No Counter Found for the ID provided")

            token_for = Tokens.TokenCreatedFor.Department
            with transaction.atomic():
                if counter_wise_token:
                    token_for = Tokens.TokenCreatedFor.Counter
                    last_token = Tokens.objects.filter(department=department, counter=counter,token_created_for=today).order_by("token_no").select_for_update(nowait=True).first()
                else:
                    last_token = Tokens.objects.filter(department=department, token_created_for=today).order_by("token_no").select_for_update(nowait=True).first()
                
                next_token_no = 1
                if last_token:
                    next_token_no = last_token.token_no + 1
                
                new_token = Tokens.objects.create(
                    department=department,
                    counter=counter,
                    description=input_serializer.validated_data.get("description", "Token Created "),
                    priority_id=input_serializer.validated_data.get("priority", None),
                    token_no=next_token_no,
                    token_created_for=today,
                    token_for=token_for,
                    refered_from=None,
                )
            message = "Token Created Successfully"
            status_code = status.HTTP_201_CREATED
            res = {"data": {"token_id": new_token.id, "token_no": new_token.token_no}, "message": message, "status": status_code}

            return Response(res, status=status_code)
        except Exception as e:
            message = "There was an Error"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            res = {"data": str(e), "message": message, "status": status_code}
            return Response(res, status=status_code)

class GetCurrentServingToken(APIView):

    def get(self, request, *args, **kwargs):
        department_id = request.query_params.get("department_id", None)
        counter_id = request.query_params.get("counter_id", None)

        if not department_id:
            status_code=status.HTTP_400_BAD_REQUEST
            message="Department ID is required"
            res = {"data": [], "message": message, "status": status_code}
            return Response(res, status=status_code)

        try:
            department = Department.objects.filter(id=department_id).defer('created_at','updated_at').order_by("-id").first()
            if not department:
                status_code=status.HTTP_404_NOT_FOUND
                message="No Department Found for the ID provided"
                res = {"data": [], "message": message, "status": status_code}
                return Response(res, status=status_code)

            counter = None
            counter_wise_token = department.is_counter_queue_node

            if counter_wise_token:
                if not counter_id:
                    status_code=status.HTTP_404_NOT_FOUND
                    message="Counter ID is required for this department"
                    res = {"data": [], "message": message, "status": status_code}
                    return Response(res, status=status_code)
                counter = Counter.objects.filter(id=counter_id).select_related("department").first()
                if not counter:
                    status_code=status.HTTP_404_NOT_FOUND
                    message="No Counter Found for the ID provided"
                    res = {"data": [], "message": message, "status": status_code}
                    return Response(res, status=status_code)

            today = date.today()
            if counter_wise_token:
                current_token = Tokens.objects.filter(department=department, counter=counter, status=Tokens.TokenStatus.IN_PROGRESS, token_created_for=today).order_by("token_no").first()
            else:
                current_token = Tokens.objects.filter(department=department, status=Tokens.TokenStatus.IN_PROGRESS, token_created_for=today).order_by("token_no").first()

            if not current_token:
                status_code=status.HTTP_404_NOT_FOUND
                message="No Current Serving Token Found"
                res = {"data": [], "message": message, "status": status_code}
                return Response(res, status=status_code)

            token_data = {
                "token_id": current_token.id,
                "token_no": current_token.token_no,
                "status": current_token.status,
                "description": current_token.description,
            }
            status_code=status.HTTP_200_OK
            message="Current Serving Token Retrieved Successfully"
            res = {"data": token_data, "message": message, "status": status_code}
            return Response(res, status=status_code)
        except Exception as e:
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            message=str(e)
            res = {"data": [], "message": message, "status": status_code}
            return Response(res, status=status_code)
        

class NextTokenAPI(APIView):
    def post(self, request, *args, **kwargs):
        try:
            
            depatment_id = request.data.get("department_id", None)
            counter_id = request.data.get("counter_id", None)

            if not depatment_id:
                status_code=status.HTTP_400_BAD_REQUEST
                message="Department ID is required"
                res = {"data": [], "message": message, "status": status_code}
                return Response(res, status=status_code)

            department = Department.objects.filter(id=depatment_id).defer('created_at','updated_at').first()
            if not department:
                status_code=status.HTTP_400_BAD_REQUEST
                message="No Department Found for the ID provided"
                res = {"data": [], "message": message, "status": status_code}
                return Response(res, status=status_code)
                
            counter = None
            counter_wise_token = department.is_counter_queue_node
            if counter_wise_token:
                if not counter_id:
                    status_code=status.HTTP_400_BAD_REQUEST
                    message="Counter ID is required for this department"
                    res = {"data": [], "message": message, "status": status_code}
                    return Response(res, status=status_code)
                counter = Counter.objects.filter(id=counter_id).select_related("department").first()
                if not counter:
                    status_code=status.HTTP_400_BAD_REQUEST
                    message="No Counter Found for the ID provided"
                    res = {"data": [], "message": message, "status": status_code}
                    return Response(res, status=status_code)
            
            today = date.today()
            with transaction.atomic():
                current_serving_token = Tokens.objects.filter(department=department, status=Tokens.TokenStatus.IN_PROGRESS).order_by("token_no").first()
                if current_serving_token:
                    current_serving_token.status = Tokens.TokenStatus.CLOSED
                    current_serving_token.save()

                if counter_wise_token:
                    next_token = Tokens.objects.filter(department=department, counter=counter, status=Tokens.TokenStatus.OPEN, token_created_for=today).order_by("token_no").select_for_update(nowait=True).first()
                else:
                    next_token = Tokens.objects.filter(department=department, status=Tokens.TokenStatus.OPEN, token_created_for=today).order_by("token_no").select_for_update(nowait=True).first()
                
                if not next_token:
                    status_code=status.HTTP_400_BAD_REQUEST
                    message="No Next Token Available"
                    res = {"data": [], "message": message, "status": status_code}
                    return Response(res, status=status_code)
                
                next_token.status = Tokens.TokenStatus.IN_PROGRESS
                next_token.save()
            message = "Next Token Retrieved Successfully"
            status_code = status.HTTP_200_OK
            res = {"data": {"token_id": next_token.id, "token_no": next_token.token_no}, "message": message, "status": status_code}
                
            send_token_display_update(data = {
                "current_token_no": next_token.token_no,
                "status": next_token.status,
                "department_id": department.id,
                "counter_id": counter.id if counter else None
            })
            
            return Response(res, status=status_code)

        except Exception as e:
            message = "There was an Error"
            status_code = status.HTTP_400_BAD_REQUEST
            res = {"data": str(e), "message": message, "status": status_code}
            return Response(res, status=status_code)

