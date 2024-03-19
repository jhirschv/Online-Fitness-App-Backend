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
        fields = ['username', 'id']

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(write_only=True, required=False)  # Not required if you're updating and not changing the exercise
    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'exercise', 'exercise_name', 'sets', 'reps', 'note']  

    def create(self, validated_data):
        exercise_name = validated_data.pop('exercise_name', None)
        
        # If an exercise name is provided, use it to get or create an Exercise instance
        if exercise_name:
            exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            validated_data['exercise'] = exercise
        
        workout_exercise = WorkoutExercise.objects.create(**validated_data)
        return workout_exercise

    def update(self, instance, validated_data):
        exercise_name = validated_data.pop('exercise_name', None)

        # If an exercise name is provided, use it to get or create an Exercise instance
        if exercise_name:
            instance.exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            instance.exercise.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class WorkoutSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    workout_exercises = WorkoutExerciseSerializer(many=True)

    class Meta:
        model = Workout
        fields = '__all__'

    def create(self, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises')
        workout = Workout.objects.create(**validated_data)
        for workout_exercise_data in workout_exercises_data:
            workout_exercise_serializer = WorkoutExerciseSerializer(data=workout_exercise_data)
            if workout_exercise_serializer.is_valid(raise_exception=True):
                workout_exercise_serializer.save(workout=workout)
        return workout

    def update(self, instance, validated_data):
        workout_exercises_data = validated_data.pop('workout_exercises', [])
        
        # Update the Workout instance itself
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Clear existing workout_exercises and recreate them
        # This is a simple approach; for more complex scenarios, you might update existing instances
        instance.workout_exercises.all().delete()

        # Handle creating new WorkoutExercise instances
        for workout_exercise_data in workout_exercises_data:
            exercise_name = workout_exercise_data.pop('exercise_name', None)
            exercise = None
            if exercise_name:
                exercise, created = Exercise.objects.get_or_create(name=exercise_name)
            
            WorkoutExercise.objects.create(workout=instance, exercise=exercise, **workout_exercise_data)

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
        fields = ['id', 'exercise_log', 'set_number', 'reps', 'weight_used', 'video']

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

class PhaseDetailSerializer(serializers.ModelSerializer):
    workouts_by_week = serializers.SerializerMethodField()

    class Meta:
        model = Phase
        fields = ['id', 'name', 'workouts_by_week']

    def get_workouts_by_week(self, phase):
        weeks_data = []
        workouts = WorkoutSerializer(phase.workouts.all(), many=True).data
        for week_number in range(1, phase.weeks + 1):
            week_data = {
                'week': week_number,
                'workouts': workouts
            }
            weeks_data.append(week_data)
        return weeks_data