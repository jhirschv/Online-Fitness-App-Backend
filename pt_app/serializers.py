from rest_framework import serializers
from .models import Exercise, Workout

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['name']

class WorkoutSerializer(serializers.ModelSerializer):
    exercises = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )
    
    class Meta:
        model = Workout
        fields = ['id', 'name', 'exercises']

    def create(self, validated_data):
        exercise_names = validated_data.pop('exercises')
        workout = Workout.objects.create(**validated_data)
        for name in exercise_names:
            exercise, created = Exercise.objects.get_or_create(name=name)
            workout.exercises.add(exercise)
        return workout

   