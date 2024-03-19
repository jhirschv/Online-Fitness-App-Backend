from django.utils import timezone
from django.db import transaction
from .models import Program, Phase, Workout, Exercise, WorkoutExercise, User, UserProgramProgress, PhaseProgress, WorkoutSession, ExerciseLog, ExerciseSet
from django.conf import settings

def set_or_update_user_program_progress(user, program_id):
    program = Program.objects.get(id=program_id)

    UserProgramProgress.objects.filter(user=user, is_active=True).exclude(program=program).update(is_active=False)
    
    user_program_progress, created = UserProgramProgress.objects.get_or_create(
        user=user,
        program=program,
        defaults={
            'current_phase': program.phases.first(),  # Assuming you want to start with the first phase
            'is_active': True,
            'start_date': timezone.now(),
        }
    )
    
    if not created:
        # If an existing progress is found, simply ensure it's marked as active
        user_program_progress.is_active = True 
        user_program_progress.save()

    return user_program_progress

def get_current_workout(user):
    try:
        program_progress = UserProgramProgress.objects.get(user=user, is_active=True)
        
        # Try to get the PhaseProgress for the current phase
        phase_progress, created = PhaseProgress.objects.get_or_create(
            user_program_progress=program_progress, 
            phase=program_progress.current_phase,
            defaults={'current_week': 1}
        )

        # If there is no current workout set, find the first workout and set it
        if not phase_progress.current_workout_id:
            # Assuming phases are ordered and the first phase has at least one workout
            first_workout = Workout.objects.filter(phase=program_progress.current_phase).order_by('id').first()
            if first_workout:
                phase_progress.current_workout_id = first_workout
                phase_progress.save()
            else:
                return None  # Handle the case where there are no workouts
            
        return phase_progress.current_workout_id
    except UserProgramProgress.DoesNotExist:
        # Optionally, handle the case where the user has no program progress, e.g., by creating it or returning None
        return None
    
def start_workout_session(user, workout_id):
    with transaction.atomic():
        user_program_progress = UserProgramProgress.objects.get(user=user, is_active=True)
        workout_session = WorkoutSession.objects.create(
            user_program_progress=user_program_progress,
            workout_id=workout_id,
            completed=False
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
                    reps=0,
                    weight_used=None
                )
    return workout_session
