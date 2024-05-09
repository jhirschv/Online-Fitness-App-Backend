from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings

class User(AbstractUser):
    public_key = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.username

class Program(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, related_name='created_programs', on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='participating_programs', blank=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Workout(models.Model):
    program = models.ForeignKey(Program, related_name='workouts', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    creator = models.ForeignKey(User, related_name='created_workouts', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_ai_generated = models.BooleanField(default=False)  # Indicates if the workout is AI-generated
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Exercise(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='No description')
    video = models.CharField(max_length=255, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, related_name='workout_exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, related_name='workout_exercises', on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.exercise.name

class UserProgramProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_programs')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='active_users')
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s progress in {self.program.name}"

class WorkoutSession(models.Model):
    user_program_progress = models.ForeignKey(UserProgramProgress, on_delete=models.CASCADE, related_name='workout_sessions')
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateTimeField(default=now, editable=True)
    completed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"ID: {self.id} - {self.user_program_progress.user.username}'s session: {self.workout.name} on {self.date.strftime('%Y-%m-%d')}"

class ExerciseLog(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, related_name='exercise_logs', on_delete=models.CASCADE)
    workout_exercise = models.ForeignKey(WorkoutExercise, on_delete=models.CASCADE)
    sets_completed = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)   

    def __str__(self):
        return f"Log for {self.workout_exercise.exercise.name} in session {self.workout_session.id}"
    
class ExerciseSet(models.Model):
    exercise_log = models.ForeignKey(ExerciseLog, related_name='exercise_sets', on_delete=models.CASCADE)
    set_number = models.IntegerField()
    reps = models.IntegerField(null=True, blank=True)
    weight_used = models.IntegerField(null=True, blank=True)
    video = models.FileField(upload_to='workout_videos/', blank=True, null=True)
    is_logged = models.BooleanField(default=False)


    class Meta:
        ordering = ['set_number']

    def __str__(self):
        return f"Set {self.set_number} for {self.exercise_log.workout_exercise.exercise.name}"
    
#Chat_Feature
class ChatSession(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chats', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatSession {self.pk}"

class Message(models.Model):
    chat_session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    encrypted_message_recipient = models.TextField(null=True, blank=True)
    encrypted_message_sender = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} on {self.timestamp}"


