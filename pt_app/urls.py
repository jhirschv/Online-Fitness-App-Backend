from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MyTokenObtainPairView
from rest_framework.routers import DefaultRouter
from .views import (ProgramViewSet, WorkoutViewSet, ExerciseViewSet, WorkoutExerciseViewSet, UserProgramViewSet, 
ProgramCreateView, ActiveProgramView, SetActiveProgramView, StartWorkoutSessionView, WorkoutSessionDetailView,
 UserWorkoutSessionView, ExerciseSetViewSet, UserWorkoutViewSet, SetInactiveProgramView, CreateAndActivateProgramView,
 OpenAIView, UserViewSet, MessageViewSet, ChatSessionViewSet, WorkoutSessionsLast3MonthsView , Exercise1RMView, ExercisesWithWeightsView, CumulativeWeightView,
 check_active_session, EndWorkoutSession, VideoUploadAPI, DeleteVideoAPIView, ExerciseSetHistoryView, ExerciseLogViewSet, ExerciseSetCreateAPIView,
 DeleteLastExerciseSetAPIView, UpdateWorkoutOrderAPIView, UpdateExerciseOrderAPIView, OpenAIProgramView)

router = DefaultRouter()
router.register(r'programs', ProgramViewSet)
router.register(r'user_programs', UserProgramViewSet, basename='user_program')
router.register(r'workouts', WorkoutViewSet)
router.register(r'user_workouts', UserWorkoutViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'workout_exercises', WorkoutExerciseViewSet)
router.register(r'user_workout_sessions', UserWorkoutSessionView, basename='userworkoutsession')
router.register(r'users', UserViewSet)
router.register(r'messages', MessageViewSet, basename='messages')
router.register(r'chat_sessions', ChatSessionViewSet, basename='chat_session')

urlpatterns = [
    path('', include(router.urls)),
    path('create_program/', ProgramCreateView.as_view(), name='program-create'),
    path('update_workout_order/', UpdateWorkoutOrderAPIView.as_view(), name='update_workout_exercise_order'),
    path('update_exercise_order/', UpdateExerciseOrderAPIView.as_view(), name='update_exercise_order'),
    path('get_active_program/', ActiveProgramView.as_view(), name='get_active_program'),
    path('set_active_program/', SetActiveProgramView.as_view(), name='set_active_program'),
    path('set_inactive_program/', SetInactiveProgramView.as_view(), name='set_inactive_program'),
    path('create-and-activate/', CreateAndActivateProgramView.as_view(), name='create_and_activate_program'),
    path('start_workout_session/', StartWorkoutSessionView.as_view(), name='start-workout-session'),
    path('check_active_session/', check_active_session, name='check-active-session'),
    path('end-session/<int:session_id>/', EndWorkoutSession.as_view(), name='end_workout_session'),
    path('workoutSession/<int:id>/', WorkoutSessionDetailView.as_view(), name='workout-session-detail'),
    path('exercise_set_update/<int:pk>/', ExerciseSetViewSet.as_view(), name='exercise_set_update'),
    path('exercise-logs/<int:log_id>/exercise-sets/', ExerciseSetCreateAPIView.as_view(), name='exercise-set-create'),
    path('exercise-logs/<int:log_id>/delete-last-set/', DeleteLastExerciseSetAPIView.as_view(), name='delete-last-set'),
    path('exercise_log_update/<int:pk>/', ExerciseLogViewSet.as_view(), name='exercise_log_update'),
    path('upload_video/<int:set_id>/', VideoUploadAPI.as_view(), name='upload_video'),
    path('delete_video/<int:set_id>/', DeleteVideoAPIView.as_view(), name='delete-video'),
    path('exercise-sets/history/<int:exercise_id>/', ExerciseSetHistoryView.as_view(), name='exercise-set-history'),
    path('api/openai/', OpenAIView.as_view(), name='openai-api'),
    path('api/openaiprogram/', OpenAIProgramView.as_view(), name='openai-api'),
    path('chat/<int:other_user_id>/', views.ChatSessionViewSet.as_view({'get': 'list'}), name='chat-session', ),
    path('workout_sessions_last_3_months/', WorkoutSessionsLast3MonthsView.as_view(), name='workout_sessions_last_3_months'),
    path('exercise/<int:exercise_id>/1rm/', Exercise1RMView.as_view(), name='exercise-1rm'),
    path('exercises_with_weights/', ExercisesWithWeightsView.as_view(), name='exercises-with-weights'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('cumulative-weight/', CumulativeWeightView.as_view(), name='cumulative-weight'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls')),
]

 