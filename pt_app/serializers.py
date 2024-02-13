from rest_framework import serializers
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    # Explicitly serialize the related Exercise using ExerciseSerializer
    exercise = ExerciseSerializer(read_only=True)
    
    class Meta:
        model = WorkoutExercise
        fields = '__all__'

class WorkoutSerializer(serializers.ModelSerializer):
    # Serialize nested WorkoutExercises within each Workout
    workout_exercises = WorkoutExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = '__all__'

class PhaseSerializer(serializers.ModelSerializer):
    # Serialize nested Workouts within each Phase
    workouts = WorkoutSerializer(many=True, read_only=True)

    class Meta:
        model = Phase
        fields = '__all__'

class ProgramSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    phases = PhaseSerializer(many=True, read_only=True)

    class Meta:
        model = Program
        fields = '__all__'