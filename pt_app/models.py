from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    
    def __str__(self):
        return self.username

class Program(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(User, related_name='created_programs', on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='participating_programs', blank=True)

    def __str__(self):
        return self.name

class Phase(models.Model):
    program = models.ForeignKey(Program, related_name='phases', on_delete=models.CASCADE)
    name = models.CharField(max_length=120, default='No Name')
    weeks = models.IntegerField()

    def __str__(self):
        return f"{self.program} Phase {self.name}"

class Workout(models.Model):
    phase = models.ForeignKey(Phase, related_name='workouts', on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Exercise(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='No description')

    def __str__(self):
        return self.name

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, related_name='workout_exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, related_name='workout_exercises', on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    video = models.URLField(blank=True, null=True)


