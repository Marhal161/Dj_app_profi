from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse
from django.shortcuts import redirect

class LogoutView(APIView):
    @staticmethod
    def get(request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            response = Response({
                'success': True,
                'message': 'Вы успешно вышли из системы',
            }, status=status.HTTP_200_OK)

            response.delete_cookie('access_token', path='/')
            response.delete_cookie('refresh_token', path='/')

            response["Access-Control-Allow-Credentials"] = "true"

            return response
        
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        
            
                
                