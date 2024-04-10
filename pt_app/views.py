from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import (Program, Phase, Workout, Exercise, WorkoutExercise, UserProgramProgress, PhaseProgress, WorkoutSession, ExerciseLog, ExerciseSet, 
                    User, Message, ChatSession)
from .serializers import (MyTokenObtainPairSerializer, ProgramSerializer, PhaseSerializer, WorkoutSerializer, ExerciseSerializer, WorkoutExerciseSerializer, 
                        WorkoutSessionSerializer, PhaseDetailSerializer, ExerciseSetSerializer, UserSerializer, MessageSerializer, ChatSessionSerializer)
from .utils import set_or_update_user_program_progress, get_current_workout, start_workout_session, get_chat_session, get_messages_for_session
from rest_framework import status
import openai
import json
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from collections import OrderedDict

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

class PhaseViewSet(viewsets.ModelViewSet):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer

class WorkoutViewSet(viewsets.ModelViewSet):
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
class UserWorkoutViewSet(viewsets.ModelViewSet):
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer

    def get_queryset(self):
        return Workout.objects.filter(creator=self.request.user)

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer

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
                return Response({'message': 'Program created and set as active successfully.'}, status=status.HTTP_201_CREATED)
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
        
class CurrentWorkoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        current_workout = get_current_workout(request.user)
        if current_workout:
            serializer = WorkoutSerializer(current_workout)
            return Response(serializer.data)
        else:
            return Response({'message': 'No current workout found.'}, status=404)
        
class StartWorkoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        workout_id = request.data.get('workout_id')
        try:
            workout_session = start_workout_session(request.user, workout_id)
            return Response({'message': 'Workout session started successfully.', 'session_id': workout_session.id})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
class UserWorkoutSessionView(viewsets.ModelViewSet):
    serializer_class = WorkoutSessionSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkoutSession.objects.filter(user_program_progress__user=self.request.user)
        
class WorkoutSessionDetailView(RetrieveAPIView):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionSerializer
    lookup_field = 'id'

class PhasesDetailView(APIView):
    #permission_classes = [IsAuthenticated]

    def get(self, request, program_id):
        program = get_object_or_404(Program, pk=program_id)
        phases = program.phases.all()
        serializer = PhaseDetailSerializer(phases, many=True)
        return Response(serializer.data)
    
class UpdateWorkoutProgressView(APIView):
    # Assuming you have permission_classes defined elsewhere

    def post(self, request):
        user = request.user
        phase_id = request.data.get('phase_id')
        week_number = request.data.get('week_number')
        workout_id = request.data.get('workout_id')

        with transaction.atomic():
            user_prog_progress = UserProgramProgress.objects.get(user=user, is_active=True)
            workout = Workout.objects.get(id=workout_id)  # Get the Workout instance
            
            phase_prog, _ = PhaseProgress.objects.get_or_create(
                user_program_progress=user_prog_progress, 
                phase_id=phase_id,
                defaults={'current_week': week_number, 'current_workout_id': workout}
            )
            
            user_prog_progress.current_phase_id = phase_id
            user_prog_progress.save()
            
            phase_prog.current_week = week_number
            phase_prog.current_workout_id = workout  # Update to directly reference the Workout instance
            phase_prog.save()

            return Response({'status': 'success', 'message': 'Workout progress updated'})

class ExerciseSetViewSet(RetrieveUpdateAPIView):
    queryset = ExerciseSet.objects.all()
    serializer_class = ExerciseSetSerializer

    def perform_update(self, serializer):
    # Custom update logic here
        serializer.save()


#openai api


class OpenAIView(APIView):
    def post(self, request, *args, **kwargs):
        user_prompt = request.data.get('prompt')
        if not user_prompt:
            return Response({"error": "No prompt provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            openai.api_key = settings.API_KEY
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
        {
            "role": "system",
            "content": "You are Professional NSCA Certified Strength and Conditioning Specialist. Write a workout based on the user's prompts following all NSCA guidelines. Your response should be a valid JSON object structured as follows: "
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

            serializer = WorkoutSerializer(data=workout_data, context={'request': request})
            if serializer.is_valid():
                serializer.save(creator=request.user)  # Assuming your Workout model has a creator field
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
            week_str = current_date.strftime('%Y-%U')  # Year and week number
            data[week_str] = 0
            current_date += timedelta(days=7)

        for session in sessions:
            week_str = session.date.strftime('%Y-%U')
            if week_str in data:
                data[week_str] += 1

        # Convert to a format suitable for Recharts
        chart_data = [{'week': week, 'workouts': count} for week, count in data.items()]
        return chart_data