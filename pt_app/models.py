from django.db import models
     
class Exercise(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Workout(models.Model):
    name = models.CharField(max_length=50)
    exercises = models.ManyToManyField(Exercise, related_name='workouts')

    def __str__(self):
        return self.name