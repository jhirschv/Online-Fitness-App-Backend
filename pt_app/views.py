from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Workout, Exercise
from .serializers import WorkoutSerializer, ExerciseSerializer
from rest_framework import status

def test_api(request):
    data = {'message': 'Hello from Django!'}
    return JsonResponse(data)

class WorkoutList(APIView):
    def get(self, request, format=None):
        workouts = Workout.objects.all()
        serializer = WorkoutSerializer(workouts, many=True)
        return Response(serializer.data)
    
class ExerciseList(APIView):
    def get(self, request, id, format=None):
        try:
            workout = Workout.objects.get(id=id)
        except Workout.DoesNotExist:
            return Response({"error": "Workout not found"}, status=404)
        
        exercises = workout.exercises.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return Response(serializer.data)
    
class Exercises(APIView):
    def get(self, request, format=None):
        exercises = Exercise.objects.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return Response(serializer.data)
    
class ExerciseCreate(APIView):
    def post(self, request, format=None):
        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class WorkoutCreate(APIView):
    def post(self, request, format=None):
        serializer = WorkoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)