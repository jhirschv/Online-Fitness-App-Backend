from rest_framework import serializers
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, User, WorkoutSession, ExerciseLog, ExerciseSet
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
        fields = '__all__'

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(), source='exercise', write_only=True
    )

    class Meta:
        model = WorkoutExercise
        fields = '__all__'  # Make sure to include 'exercise' and 'exercise_id'

    def create(self, validated_data):
        # This method might be adjusted based on your exact requirements
        return WorkoutExercise.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Similarly, adjust this method as needed
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class WorkoutSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseSerializer(many=True)

    class Meta:
        model = Workout
        fields = '__all__'

    def create(self, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises')
        workout = Workout.objects.create(**validated_data)
        for workout_exercise_data in workout_exercises_data:
            WorkoutExercise.objects.create(workout=workout, **workout_exercise_data)
        return workout

    def update(self, instance, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises')
        # Update the workout instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle updating or creating workout exercises
        for workout_exercise_data in workout_exercises_data:
            exercise_id = workout_exercise_data.get('exercise').id
            workout_exercise_instance, created = WorkoutExercise.objects.update_or_create(
                workout=instance, exercise_id=exercise_id,
                defaults=workout_exercise_data
            )

        return instance
    
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

#workout journal feature
        
class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['set_number', 'reps', 'weight_used', 'video']

class ExerciseLogSerializer(serializers.ModelSerializer):
    sets = ExerciseSetSerializer(many=True, read_only=True, source='exercise_sets')
    workout_exercise = WorkoutExerciseSerializer(read_only=True)

    class Meta:
        model = ExerciseLog
        fields = ['id', 'workout_exercise', 'sets_completed', 'note', 'sets']

class WorkoutSessionSerializer(serializers.ModelSerializer):
    workout = WorkoutSerializer(read_only=True)
    exercise_logs = ExerciseLogSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutSession
        fields = ['id', 'workout', 'date', 'completed', 'exercise_logs']