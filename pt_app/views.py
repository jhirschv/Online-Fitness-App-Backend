from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import (Program, Workout, Exercise, WorkoutExercise, UserProgramProgress, WorkoutSession, ExerciseLog, ExerciseSet, 
                    User, Message, ChatSession)
from .serializers import (MyTokenObtainPairSerializer, ProgramSerializer, WorkoutSerializer, ExerciseSerializer, WorkoutExerciseSerializer, 
                        WorkoutSessionSerializer, ExerciseSetSerializer, UserSerializer, MessageSerializer, ChatSessionSerializer,
                        ExerciseSetVideoSerializer, ExerciseLogSerializer, WorkoutOrderSerializer, ExerciseOrderSerializer)
from .utils import set_or_update_user_program_progress, start_workout_session, get_chat_session, get_messages_for_session
from rest_framework import status
import openai
import json
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from collections import OrderedDict
from django.db.models import Exists, OuterRef
from rest_framework.decorators import api_view, permission_classes
from django.core.exceptions import ObjectDoesNotExist

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class UserProgramViewSet(viewsets.ModelViewSet):
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Program.objects.filter(creator=self.request.user)

class WorkoutViewSet(viewsets.ModelViewSet):
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class UpdateWorkoutOrderAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = WorkoutOrderSerializer(data=request.data, many=True)
        if serializer.is_valid():
            updates = []
            errors = []
            for item in serializer.validated_data:
                try:
                    workout = Workout.objects.get(id=item['id'])
                    workout.order = item['order']
                    workout.save()
                    updates.append({'id': workout.id, 'order': workout.order})
                except ObjectDoesNotExist:
                    errors.append({'id': item['id'], 'error': 'Workout does not exist'})
            
            if errors:
                return Response({'status': 'partial_success', 'updated': updates, 'errors': errors}, status=status.HTTP_206_PARTIAL_CONTENT)
            return Response({'status': 'success', 'updated': updates}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UpdateExerciseOrderAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ExerciseOrderSerializer(data=request.data, many=True)
        if serializer.is_valid():
            for item in serializer.validated_data:
                exercise = WorkoutExercise.objects.get(id=item['id'])
                exercise.order = item['order']
                exercise.save()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserWorkoutViewSet(viewsets.ModelViewSet):
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        return Workout.objects.filter(creator=self.request.user)

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

class ExerciseSetCreateAPIView(APIView):
    def post(self, request, log_id):
        # Retrieve the associated ExerciseLog
        exercise_log = ExerciseLog.objects.get(id=log_id)

        # Determine the next set number
        if exercise_log.exercise_sets.count() > 0:
            last_set_number = exercise_log.exercise_sets.last().set_number
        else:
            last_set_number = 0

        new_set_number = last_set_number + 1

        # Create a new ExerciseSet with the next set number
        exercise_set = ExerciseSet(
            exercise_log=exercise_log,
            set_number=new_set_number,
            reps=request.data.get('reps', None),  # Optional data from request
            weight_used=request.data.get('weight_used', None)  # Optional data from request
        )
        exercise_set.save()

        # Optionally update the ExerciseLog sets_completed field
        exercise_log.sets_completed += 1
        exercise_log.save()

        # Serialize and return the new ExerciseSet
        serializer = ExerciseSetSerializer(exercise_set)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class DeleteLastExerciseSetAPIView(APIView):
    def delete(self, request, log_id):
        try:
            exercise_log = ExerciseLog.objects.get(id=log_id)
        except ExerciseLog.DoesNotExist:
            return Response({'error': 'Exercise log not found'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the corresponding WorkoutExercise
        workout_exercise = exercise_log.workout_exercise

        # Get the last ExerciseSet
        last_exercise_set = exercise_log.exercise_sets.order_by('set_number').last()

        if last_exercise_set:
            # Check if the current number of sets in the log exceeds the defined number of sets in the workout
            if exercise_log.exercise_sets.count() > workout_exercise.sets:
                last_exercise_set.delete()
                # Update sets_completed if necessary
                exercise_log.sets_completed = max(0, exercise_log.sets_completed - 1)
                exercise_log.save()
                return Response({'message': 'Last set deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Cannot delete the set. The number of sets does not exceed the workout plan.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No sets to delete'}, status=status.HTTP_404_NOT_FOUND)

class VideoUploadAPI(APIView):
    def patch(self, request, set_id):
        try:
            exercise_set = ExerciseSet.objects.get(id=set_id)
            serializer = ExerciseSetVideoSerializer(exercise_set, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Video uploaded successfully', 'status': 'success'}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExerciseSet.DoesNotExist:
            return Response({'error': 'ExerciseSet not found'}, status=status.HTTP_404_NOT_FOUND)
        
class DeleteVideoAPIView(APIView):
    def delete(self, request, set_id):
        try:
            exercise_set = ExerciseSet.objects.get(id=set_id)
            exercise_set.video.delete()  # This deletes the file from storage and removes the association
            exercise_set.video = None  # Ensure the field is set to None after deletion
            exercise_set.save()
            return Response({'message': 'Video deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except ExerciseSet.DoesNotExist:
            return Response({'error': 'ExerciseSet not found'}, status=status.HTTP_404_NOT_FOUND)

class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    queryset = WorkoutExercise.objects.all()
    serializer_class = WorkoutExerciseSerializer

class ProgramCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ProgramSerializer(data=request.data)
        if serializer.is_valid():
            # Manually set the creator to the currently authenticated user
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#APIs for Workout Journal

class SetActiveProgramView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        program_id = request.data.get('program_id')
        if not program_id:
            return Response({'error': 'Program ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_program_progress = set_or_update_user_program_progress(request.user, program_id)
            return Response({'message': 'Program set as active successfully.'})
        except Program.DoesNotExist:
            return Response({'error': 'Program not found.'}, status=status.HTTP_404_NOT_FOUND)

class SetInactiveProgramView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        program_id = request.data.get('program_id')
        if not program_id:
            return Response({'error': 'Program ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Attempt to retrieve the program and the user's program progress.
            program = Program.objects.get(id=program_id)
            user_program_progress = UserProgramProgress.objects.get(user=request.user, program=program)
            
            # Set the program to inactive if it's currently active.
            if user_program_progress.is_active:
                user_program_progress.is_active = False
                user_program_progress.save()
                return Response({'message': 'Program set to inactive successfully.'})
            else:
                return Response({'error': 'Program is already inactive.'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Program.DoesNotExist:
            return Response({'error': 'Program not found.'}, status=status.HTTP_404_NOT_FOUND)
        except UserProgramProgress.DoesNotExist:
            return Response({'error': 'User program progress not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class CreateAndActivateProgramView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Step 1: Create the program
        serializer = ProgramSerializer(data=request.data)
        if serializer.is_valid():
            program = serializer.save(creator=request.user)

            # Step 2: Set the program as active
            try:
                user_program_progress = set_or_update_user_program_progress(request.user, program.id)
                return Response({'message': 'Program created and set as active successfully.', 'program': ProgramSerializer(program).data}, status=status.HTTP_201_CREATED)
            except Program.DoesNotExist:  # This should theoretically never happen since we just created the program
                return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class ActiveProgramView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_program_progress = UserProgramProgress.objects.get(user=request.user, is_active=True)
            program = user_program_progress.program
            serializer = ProgramSerializer(program)
            return Response(serializer.data)
        except UserProgramProgress.DoesNotExist:
            return Response({'error': 'No active program found.'}, status=status.HTTP_404_NOT_FOUND)
        
class StartWorkoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        workout_id = request.data.get('workout_id')
        try:
            # Ensure there is no other active session
            if WorkoutSession.objects.filter(
                user_program_progress__user=request.user,
                user_program_progress__is_active=True,
                active=True
            ).exists():
                return Response({'error': 'Another workout session is already active.'}, status=400)

            workout_session = start_workout_session(request.user, workout_id)
            return Response({'message': 'Workout session started successfully.', 'session_id': workout_session.id})

        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_active_session(request):
    current_user = request.user
    active_session = WorkoutSession.objects.filter(
        user_program_progress__user=current_user,
        active=True,
        completed=False
    ).first()

    if active_session:
        # Serialize the active session
        serializer = WorkoutSessionSerializer(active_session)
        return Response(serializer.data)
    else:
        # If no active session is found, return a different response
        return Response({'active': False})
    
class EndWorkoutSession(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = WorkoutSession.objects.get(id=session_id)
            if not session.completed:
                session.completed = True
                session.active = False
                session.save()
                return Response({'status': 'success', 'message': 'Workout session ended successfully.'})
            else:
                return Response({'status': 'error', 'message': 'Session already completed.'}, status=status.HTTP_400_BAD_REQUEST)
        except WorkoutSession.DoesNotExist:
            return Response({'status': 'error', 'message': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class UserWorkoutSessionView(viewsets.ModelViewSet):
    serializer_class = WorkoutSessionSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkoutSession.objects.filter(user_program_progress__user=self.request.user)
        
class WorkoutSessionDetailView(RetrieveAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionSerializer
    lookup_field = 'id'
        
class ExerciseLogViewSet(RetrieveUpdateAPIView):
    queryset = ExerciseLog.objects.all()
    serializer_class = ExerciseLogSerializer

    def perform_update(self, serializer):
    # Custom update logic here
        serializer.save()

class ExerciseSetViewSet(RetrieveUpdateAPIView):
    queryset = ExerciseSet.objects.all()
    serializer_class = ExerciseSetSerializer

    def perform_update(self, serializer):
    # Custom update logic here
        serializer.save()

class ExerciseSetHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        # Filter WorkoutExercises by exercise_id
        workout_exercises = WorkoutExercise.objects.filter(exercise__id=exercise_id)

        # Retrieve all the ExerciseLog ids associated with these WorkoutExercises
        workout_exercises_ids = [we.id for we in workout_exercises]

        # Fetch ExerciseSets linked through these WorkoutExercises ids and filter by weight_used not null or zero
        exercise_sets = ExerciseSet.objects.filter(
            exercise_log__workout_exercise__id__in=workout_exercises_ids,
            exercise_log__workout_session__user_program_progress__user=request.user,
            weight_used__gt=0  # Filters out ExerciseSets where weight_used is greater than 0
        )
        serializer = ExerciseSetSerializer(exercise_sets, many=True)
        return Response(serializer.data)


#openai api


class OpenAIView(APIView):
    def post(self, request, *args, **kwargs):
        user_prompt = request.data.get('prompt')
        program_id = request.data.get('program_id')

        if not user_prompt or not program_id:
            return Response({"error": "Missing prompt or phase"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            openai.api_key = settings.API_KEY
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
        {
            "role": "system",
            "content": "You are Professional NSCA Certified Strength and Conditioning Specialist. Write a workout based on the user's prompts following all NSCA guidelines. If the users prompt contains text that is unrelated, send them back the infamous One Punch Man workout formatted in the data structure that follows(100 situps, 100 pushups, 100 squats, and a 10-km run). Your response should be a valid JSON object structured as follows: "
                       "{"
                       "\"workout_exercises\": ["
                       "    {"
                       "        \"exercise_name\": \"<Name of the exercise>\","
                       "        \"sets\": <int>,"
                       "        \"reps\": <int>,"
                       "        \"note\": \"<Any specific note for the exercise>\""
                       "    },"
                       "    {...additional exercises}"
                       "],"
                       "\"name\": \"<Name of the workout program>\""
                       "}. Use double quotes for keys and string values. Replace placeholder text with actual exercise details."
        },
        {"role": "user", "content": user_prompt}
    ]
            )
            workout_data = json.loads(response.choices[0].message.content)
            workout_data['program'] = program_id

            serializer = WorkoutSerializer(data=workout_data, context={'request': request})
            if serializer.is_valid():
                serializer.save(creator=request.user)  # Assuming your Workout model has a creator field
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class OpenAIProgramView(APIView):
    def post(self, request, *args, **kwargs):
        user_prompt = request.data.get('prompt')

        if not user_prompt:
            return Response({"error": "Missing prompt"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            openai.api_key = settings.API_KEY
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
        {
        "role": "system",
        "content": "You are a Professional NSCA Certified Strength and Conditioning Specialist. Write a workout program based on the user's prompts following all NSCA guidelines. Your response should be a valid JSON object structured as follows: {"
            "\"name\": \"<Name of the workout program>\","
            "\"description\": \"<Description of the workout program>\","
            "\"workouts\": ["
                "{"
                    "\"name\": \"<Name of the workout>\","
                    "\"workout_exercises\": ["
                        "{"
                            "\"exercise_name\": \"<Name of the exercise>\","
                            "\"sets\": <type:int>,"
                            "\"reps\": <type:int>,"
                            "\"note\": \"<Specific note for the exercise>\""
                        "},"
                        "{"
                            "\"exercise_name\": \"<Name of another exercise>\","
                            "\"sets\": <type:int>,"
                            "\"reps\": <type:int>,"
                            "\"note\": \"<Specific note for another exercise>\""
                        "}"
                        "    {...additional exercises}"
                    "]"
                "}"
                "{...additional workouts}"
            "]"
        "}. Use double quotes for keys and string values. Replace placeholder text with actual program and exercise details."
        },
        {"role": "user", "content": user_prompt}
    ]
            )
            program_data = json.loads(response.choices[0].message.content)


            serializer = ProgramSerializer(data=program_data, context={'request': request})
            if serializer.is_valid():
                serializer.save(creator=request.user)  # Assuming your program model has a creator field
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#APIs for Messages
        
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

class ChatSessionViewSet(viewsets.ViewSet):
    def list(self, request, other_user_id=None):
        chat_session = get_chat_session(request.user.id, other_user_id)
        if chat_session:
            messages = get_messages_for_session(chat_session)
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        return Response({"message": "No chat session found"}, status=404)
    
#dataCharts
    
class WorkoutSessionsLast3MonthsView(APIView):
    def get(self, request):
        end_date = now()
        start_date = end_date - timedelta(days=90)  # Approximately 3 months

        sessions = WorkoutSession.objects.filter(
            user_program_progress__user=request.user,
            date__range=(start_date, end_date)
        ).order_by('date')

        chart_data = self.process_sessions_by_week(sessions, start_date, end_date)
        return Response(chart_data)

    def process_sessions_by_week(self, sessions, start_date, end_date):
        data = OrderedDict()
        current_date = start_date
        while current_date <= end_date:
            week_str = current_date.strftime('%Y-%U')  # Maintain unique year-week identification
            data[week_str] = 0
            current_date += timedelta(days=7)
        
        end_week_str = end_date.strftime('%Y-%U')
        if end_week_str not in data:
            data[end_week_str] = 0

        for session in sessions:
            week_str = session.date.strftime('%Y-%U')
            if week_str in data:
                data[week_str] += 1

        # Convert to a format suitable for Recharts, consider transforming week_str for frontend display if needed
        chart_data = [{'week': week, 'workouts': count} for week, count in data.items()]
        return chart_data
    
class Exercise1RMView(APIView):
    def get(self, request, exercise_id):
        # Calculate the date 6 months ago from today
        six_months_ago = now() - timedelta(days=180)
        
        # Fetch exercise sets for the given exercise in the last 6 months
        exercise_sets = ExerciseSet.objects.filter(
            exercise_log__workout_exercise__exercise_id=exercise_id,
            exercise_log__workout_session__date__gte=six_months_ago
        ).select_related('exercise_log__workout_exercise__exercise').exclude(weight_used__isnull=True).exclude(reps__isnull=True).order_by('exercise_log__workout_session__date')
        
        # Prepare the data for the chart
        chart_data = self.prepare_chart_data(exercise_sets)
        
        return Response(chart_data)

    def prepare_chart_data(self, exercise_sets):
        chart_data = {}
        for exercise_set in exercise_sets:
            # Calculate 1RM using the Epley formula for each set
            one_rm = exercise_set.weight_used * (1 + exercise_set.reps / 30.0)
            day = exercise_set.exercise_log.workout_session.date.strftime('%Y-%m-%d')
            
            # If multiple sets are done on the same day, store the max 1RM
            if day not in chart_data or one_rm > chart_data[day]:
                chart_data[day] = one_rm
        
        # Convert the chart data dictionary to a list of objects
        return [{'day': day, 'one_rm': one_rm} for day, one_rm in chart_data.items()]
    
class ExercisesWithWeightsView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request):
        user = request.user
        
        # Adjusted subquery to check for ExerciseSets linked to the user's WorkoutExercises
        has_weighted_sets = ExerciseSet.objects.filter(
            exercise_log__workout_session__user_program_progress__user=user,
            exercise_log__workout_exercise__exercise_id=OuterRef('pk'),  # Note the change here
            weight_used__isnull=False
        )

        # Query for Exercises with at least one ExerciseSet with weight_used for the user
        exercises = Exercise.objects.annotate(
            has_weighted_set=Exists(has_weighted_sets)
        ).filter(has_weighted_set=True).distinct()
        
        # Prepare and return the response with Exercise details
        exercises_data = [{'id': exercise.id, 'name': exercise.name} for exercise in exercises]
        return Response(exercises_data)
    
class CumulativeWeightView(APIView):
    def get(self, request):
        user = request.user  # Assuming you have user authentication set up
        end_date = now().date()
        start_date = end_date - timedelta(days=6)  # Last 7 days including today

        # Fetch all sessions for the user in the last 7 days
        sessions = WorkoutSession.objects.filter(
            user_program_progress__user=user,
            date__date__range=(start_date, end_date)
        ).prefetch_related('exercise_logs__exercise_sets')

        # Prepare data structure for cumulative weights
        cumulative_weights = {date.strftime('%Y-%m-%d'): 0 for date in [start_date + timedelta(days=x) for x in range((end_date-start_date).days + 1)]}

        # Calculate cumulative weight for each day
        for session in sessions:
            session_date = session.date.date().strftime('%Y-%m-%d')
            for log in session.exercise_logs.all():
                for exercise_set in log.exercise_sets.all():
                    if exercise_set.weight_used and exercise_set.reps:
                        cumulative_weights[session_date] += (exercise_set.weight_used * exercise_set.reps)
        
        # Format the data for the response
        response_data = [{'date': date, 'total_weight_lifted': weight} for date, weight in cumulative_weights.items()]

        return Response(response_data)