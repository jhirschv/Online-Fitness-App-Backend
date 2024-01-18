from django.db import models

class Exercise(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Workout(models.Model):
    name = models.CharField(max_length=50, default='Default Name')
    exercises = models.ManyToManyField(Exercise)

    def __str__(self):
        return f"Workout {self.id}"
