from django.shortcuts import render
from django.http import JsonResponse

def test_api(request):
    data = {'message': 'Hello from Django!'}
    return JsonResponse(data)