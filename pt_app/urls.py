from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView
from rest_framework.routers import DefaultRouter
from .views import ProgramViewSet, PhaseViewSet, WorkoutViewSet, ExerciseViewSet, WorkoutExerciseViewSet, UserProgramViewSet

router = DefaultRouter()
router.register(r'programs', ProgramViewSet)
router.register(r'user_programs', UserProgramViewSet, basename='user_program')
router.register(r'phases', PhaseViewSet)
router.register(r'workouts', WorkoutViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'workout_exercises', WorkoutExerciseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

 