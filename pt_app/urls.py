from django.urls import path
from . import views
from .views import WorkoutList, ExerciseList, ExerciseCreate

urlpatterns = [
    path('test-api/', views.test_api, name='test_api'),
    path('workouts/', WorkoutList.as_view(), name='workout_list'),
    path('exercises/', ExerciseList.as_view(), name='exercise_list'),
    path('exercise_create/', ExerciseCreate.as_view(), name='exercise_create')
]