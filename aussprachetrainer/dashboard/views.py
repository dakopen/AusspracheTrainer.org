from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from frontend.views import render_into_base
from analyze.models import PronunciationAssessmentResult
from django.db.models import Avg


@login_required
def dashboard_view(request):
    user = request.user
    averages = PronunciationAssessmentResult.objects.filter(user=user).aggregate(
        avg_accuracy=Avg('accuracy'),
        avg_fluency=Avg('fluency'), 
    )
    # TODO: Create a second database with "AusspracheTrainer Scores" that are updated
    #       every time a new PronunciationAssessmentResult is created.
    #       The latest scores are weighted more, and some also ommission are taken into
    #       account and other stuff. 
    if averages['avg_accuracy'] is None:
        averages['avg_accuracy'] = "?"
    else:
        averages['avg_accuracy'] = round(averages['avg_accuracy'])
    if averages['avg_fluency'] is None:
        averages['avg_fluency'] = "?"
    else:
        averages['avg_fluency'] = round(averages['avg_fluency'])

    context = {
        'avg_accuracy': averages['avg_accuracy'],
        'avg_fluency': averages['avg_fluency'],
        'avg_aussprachetrainer': round(90.34), # TODO: see above (mock data here)
    }


    return render_into_base(request, 'Dashboard', 'dashboard.html', context,
                            css='frontend/assets/css/dashboard.css')


# TODO: add user profile settings and move logout there (from the header)