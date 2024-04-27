from rest_framework import serializers
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, User, WorkoutSession, ExerciseLog, ExerciseSet, Message, ChatSession
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Max

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
    workout = serializers.PrimaryKeyRelatedField(queryset=Workout.objects.all(), write_only=True, required=False)

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'exercise', 'exercise_name', 'sets', 'reps', 'note', 'workout']  

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
        workout_exercises_data = validated_data.pop('workout_exercises', [])
        
        # Check if 'order' is provided, if not, determine the next order value
        if 'order' not in validated_data or validated_data['order'] is None:
            current_max_order = Workout.objects.filter(phase=validated_data['phase']).aggregate(Max('order'))['order__max']
            validated_data['order'] = (current_max_order or 0) + 1

        workout = Workout.objects.create(**validated_data)
        for workout_exercise_data in workout_exercises_data:
            workout_exercise_serializer = WorkoutExerciseSerializer(data=workout_exercise_data, context={'workout': workout})
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
        instance.workout_exercises.all().delete()
        for workout_exercise_data in workout_exercises_data:
            workout_exercise_serializer = WorkoutExerciseSerializer(data=workout_exercise_data, context={'workout': instance})
            if workout_exercise_serializer.is_valid(raise_exception=True):
                workout_exercise_serializer.save(workout=instance)

        return instance
    
class WorkoutOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    
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
        fields = ['id', 'exercise_log', 'set_number', 'reps', 'weight_used', 'video', 'is_logged']

class ExerciseSetVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['video']

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
        fields = ['id', 'workout', 'date', 'completed', 'exercise_logs', 'active']

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
    
#Message feature
    
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = '__all__'