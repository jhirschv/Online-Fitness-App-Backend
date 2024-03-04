from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, UserProgramProgress, PhaseProgress, WorkoutSession, ExerciseLog
from .serializers import MyTokenObtainPairSerializer, ProgramSerializer, PhaseSerializer, WorkoutSerializer, ExerciseSerializer, WorkoutExerciseSerializer
from .utils import set_or_update_user_program_progress
from rest_framework import status

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
            # Assuming you have a serializer for UserProgramProgress
            return Response({'message': 'Program set as active successfully.'})
        except Program.DoesNotExist:
            return Response({'error': 'Program not found.'}, status=status.HTTP_404_NOT_FOUND)
        
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
