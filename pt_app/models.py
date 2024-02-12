from django.db import models
from django.contrib.auth.models import User

class Program(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(User, related_name='created_programs', on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='participating_programs', blank=True)

class Phase(models.Model):
    program = models.ForeignKey(Program, related_name='phases', on_delete=models.CASCADE)
    number = models.IntegerField()
    weeks = models.IntegerField()

class Workout(models.Model):
    phase = models.ForeignKey(Phase, related_name='workouts', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)

class Exercise(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='No description')

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, related_name='workout_exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, related_name='workout_exercises', on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    video = models.URLField(blank=True, null=True)
