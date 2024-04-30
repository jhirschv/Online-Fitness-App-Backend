from django.utils import timezone
from django.db import transaction
from .models import (Program, Workout, Exercise, WorkoutExercise, User, UserProgramProgress, WorkoutSession, ExerciseLog, ExerciseSet,
                     ChatSession)
from django.conf import settings

def set_or_update_user_program_progress(user, program_id):
    program = Program.objects.get(id=program_id)

    # Deactivate any other active programs for this user
    UserProgramProgress.objects.filter(user=user, is_active=True).exclude(program=program).update(is_active=False)
    
    # Get or create a user program progress instance
    user_program_progress, created = UserProgramProgress.objects.get_or_create(
        user=user,
        program=program,
        defaults={
            'is_active': True,
            'start_date': timezone.now(),
        }
    )
    
    if not created:
        # If an existing progress is found, simply ensure it's marked as active
        user_program_progress.is_active = True
        user_program_progress.save()

    return user_program_progress

def start_workout_session(user, workout_id):
    with transaction.atomic():
        user_program_progress = UserProgramProgress.objects.get(user=user, is_active=True)
        workout_session = WorkoutSession.objects.create(
            user_program_progress=user_program_progress,
            workout_id=workout_id,
            completed=False,
            active=True  # Start session as active
        )

        workout_exercises = WorkoutExercise.objects.filter(workout_id=workout_id)
        for workout_exercise in workout_exercises:
            exercise_log = ExerciseLog.objects.create(
                workout_session=workout_session,
                workout_exercise=workout_exercise,
                sets_completed=0
            )

            for set_number in range(1, workout_exercise.sets + 1):
                ExerciseSet.objects.create(
                    exercise_log=exercise_log,
                    set_number=set_number,
                    reps=None,
                    weight_used=None
                )
    return workout_session

#chat feature
def get_chat_session(user_id_a, user_id_b):
    chat_sessions = ChatSession.objects.filter(
        participants__id=user_id_a
    ).filter(
        participants__id=user_id_b
    )
    
    if chat_sessions.exists():
        return chat_sessions.first()
    else:
        chat_session = ChatSession.objects.create()
        chat_session.participants.add(user_id_a, user_id_b)
        chat_session.save()
        return chat_session
    
def get_messages_for_session(chat_session):
    return chat_session.messages.all().order_by('timestamp')
