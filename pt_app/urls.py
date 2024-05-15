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
 DeleteLastExerciseSetAPIView, UpdateWorkoutOrderAPIView, UpdateExerciseOrderAPIView, OpenAIProgramView, UserRegistrationView, UserDeleteAPIView,
 UserExerciseViewSet, AIProgramLimitView, AIWorkoutLimitView, UserChatSessionsView, UpdatePublicKeyView, AddParticipantView, UserParticipatingProgramsView,
 RemoveParticipantView, SendTrainerRequestView, HandleTrainerRequestView, UserTrainerRequestsView, ClientWorkoutSessionsLast3MonthsView, 
 ClientExercise1RMView, ClientExercisesWithWeightsView, ClientCumulativeWeightView)

router = DefaultRouter()
router.register(r'programs', ProgramViewSet)
router.register(r'user_programs', UserProgramViewSet, basename='user_program')
router.register(r'workouts', WorkoutViewSet)
router.register(r'user_workouts', UserWorkoutViewSet)
router.register(r'exercises', ExerciseViewSet, basename='exercises')
router.register(r'user_exercises', UserExerciseViewSet, basename='user_exercises')
router.register(r'workout_exercises', WorkoutExerciseViewSet)
router.register(r'user_workout_sessions', UserWorkoutSessionView, basename='userworkoutsession')
router.register(r'users', UserViewSet)
router.register(r'messages', MessageViewSet, basename='messages')
router.register(r'chat_sessions', ChatSessionViewSet, basename='chat_session')

urlpatterns = [
    path('', include(router.urls)),
    path('create_program/', ProgramCreateView.as_view(), name='program-create'),
    path('programs/<int:program_id>/add-participant/', AddParticipantView.as_view(), name='add-participant'),
    path('participating/', UserParticipatingProgramsView.as_view(), name='user-participating-programs'),
    path('remove_participant/<int:program_id>/', RemoveParticipantView.as_view(), name='remove-participant'),
    path('send-trainer-request/<int:user_id>/', SendTrainerRequestView.as_view(), name='send-trainer-request'),
    path('trainer-requests/', UserTrainerRequestsView.as_view(), name='user-trainer-requests'),
    path('handle-trainer-request/<int:request_id>/', HandleTrainerRequestView.as_view(), name='handle-trainer-request'),
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
    path('ai_program_limit/', AIProgramLimitView.as_view(), name='ai_program_limit'),
    path('ai_workout_limit/', AIWorkoutLimitView.as_view(), name='ai_workout_limit'),
    path('chat/<int:other_user_id>/', views.ChatSessionMessageViewSet.as_view({'get': 'retrieve_or_create_session_get_messages'}), name='chat-session', ),
    path('user_chats/', UserChatSessionsView.as_view(), name='user_chats'),
    path('workout_sessions_last_3_months/', WorkoutSessionsLast3MonthsView.as_view(), name='workout_sessions_last_3_months'),
    path('exercise/<int:exercise_id>/1rm/', Exercise1RMView.as_view(), name='exercise-1rm'),
    path('exercises_with_weights/', ExercisesWithWeightsView.as_view(), name='exercises-with-weights'),
    path('cumulative-weight/', CumulativeWeightView.as_view(), name='cumulative-weight'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('update-public-key/', UpdatePublicKeyView.as_view(), name='update-public-key'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    path('delete-account/', UserDeleteAPIView.as_view(), name='delete-account'),
    path('client-workout-sessions-last-3-months/<int:client_id>/', ClientWorkoutSessionsLast3MonthsView.as_view(), name='client-workout-sessions-last-3-months'),
    path('client-exercise-1rm/<int:client_id>/<int:exercise_id>/', ClientExercise1RMView.as_view(), name='client-exercise-1rm'),
    path('client-exercises-with-weights/<int:client_id>/', ClientExercisesWithWeightsView.as_view(), name='client-exercises-with-weights'),
    path('client-cumulative-weight/<int:client_id>/', ClientCumulativeWeightView.as_view(), name='client-cumulative-weight'),
    
]

 