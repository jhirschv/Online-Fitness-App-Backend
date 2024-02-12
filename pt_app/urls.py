from django.urls import path
from . import views
from .views import WorkoutList, ExerciseCreate, Exercises, WorkoutCreate, ExerciseList
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView

urlpatterns = [
    path('test-api/', views.test_api, name='test_api'),
    path('workouts/', WorkoutList.as_view(), name='workout_list'),  
    path('exercises/', Exercises.as_view(), name='exercises'),
    path('exercise_create/', ExerciseCreate.as_view(), name='exercise_create'),
    path('workout_create/', WorkoutCreate.as_view(), name='workout_create'),
    path('exercises/<int:id>', ExerciseList.as_view(), name='exercise_list'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

 