from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from django.utils import translation
from django.template.loader import render_to_string
from analyze.tasks import async_pronunciation_assessment
from celery.result import AsyncResult
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import random
import uuid
from pydub import AudioSegment
import base64
import io
import os
from analyze.models import PronunciationAssessmentResult
from frontend.languages import country_class_to_locale
from django.conf import settings
from django.urls import reverse

languages = ['en-GB', 'de-DE', 'fr-FR']
random_sentences = {lang: open(os.path.join(settings.BASE_DIR, f'frontend/random_sentences/{lang.split("-")[0]}_validated.txt')).read().splitlines() for lang in languages}  # 5000 per language


def render_into_base(request, title, filepaths, context=None, content_type=None, status=None, using=None, css=None):
    """
    Render a template into the base template.
    """
    if not isinstance(filepaths, list):
        filepaths = [filepaths]

    if context is None:
        context = {}
    
    context["title"] = title
    context["filepaths"] = filepaths

    if css:
        if not isinstance(css, list):
            css = [css]
    context["css"] = css

    return render(request, 'extend_base.html', context, content_type, status, using)


def index(request):
    context = {}
    user = request.user
    
    language = request.GET.get("language")
    if language:
        context["language"] = language
    else:
        if user.is_authenticated:
            results = PronunciationAssessmentResult.objects.filter(user=user)
            latest_result = results.order_by('-created_at').first()
            context["language"] = latest_result.language if latest_result else "de-DE"
        else:
            context["language"] = "de-DE"

    return_to = request.GET.get("return_to")
    if return_to:
        if return_to == "learn":
            context["return_to"] = reverse("learn")
            context["return_to_text"] = _("Zurück zum Lernbereich")
        elif return_to == "dashboard":
            context["return_to"] = reverse("dashboard")
            context["return_to_text"] = _("Zurück zum Dashboard")


    text = request.GET.get("text")
    if text:
        context["text"] = text
    else:
        context["text"] = ""

    if context["language"] == "en-GB":
        placeholder = "Practice&nbsp;sentence"
    elif context["language"] == "fr-FR":
        placeholder = "Phrase&nbsp;d'exercice"
    elif context["language"] == "de-DE":
        placeholder = "Übungssatz"
    context["placeholder"] = placeholder

    return render_into_base(request, _("AusspracheTrainer"), ["index.html"], context,
                            css=['frontend/assets/css/index.css'])


def legal_notice(request):

    return render_into_base(request, _("Impressum"), "legal_notice.html", css=['frontend/assets/css/legal.css'])


def privacy_policy(request):
    return render_into_base(request, _("Datenschutzerklärung"), "privacy_policy.html", css=['frontend/assets/css/legal.css'])


def initiate_analysis(request):
    audio_data_url = request.POST.get('audio_data')
    text = request.POST.get('text_data')
    selected_language = request.POST.get('selected_language')

    audio_data_base64 = audio_data_url.split(',')[1]
    audio_data = base64.b64decode(audio_data_base64)
    random_name = str(uuid.uuid4()) + ".wav"

    buffer = io.BytesIO()

    audio_segment = AudioSegment.from_ogg(io.BytesIO(audio_data))
    
    if len(audio_segment) > 59000:
        audio_segment = audio_segment[:59000]  # max. 59 seconds
    audio_segment.export(buffer, format="wav")

    buffer.seek(0)

    content_file = ContentFile(buffer.read())

    
    # Save audio file to disk
    file_name = 'audio_files/' + random_name  
    default_storage.save(file_name, content_file)
    
    user_id = request.user.id if request.user.is_authenticated else None

    task = async_pronunciation_assessment.delay(file_name, text, country_class_to_locale(selected_language), user_id=user_id)
    return JsonResponse({'task_id': task.id})


def check_status(request, task_id):
    task = AsyncResult(task_id)
    response_data = {'status': task.status, 'result': task.result if task.successful() else None}
    return JsonResponse(response_data)


def analysis_error(request):

    template_content = render_to_string("result_error.html")
    return JsonResponse(template_content, safe=False)


def change_language(request):
    if not request.GET.get("lang"):
        return HttpResponse("Current language: " + translation.get_language())
    
    # strip /xx/ to xx
    lang = request.GET.get("lang").replace("/", "").replace("\\", "")
    assert lang in [code for code, name in settings.LANGUAGES]
    translation.activate(lang)
    response = HttpResponse(lang)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    return response


def generate_random_sentence(request):
    language = request.GET.get('language')
    if not language:
        language = "de-DE" # default language

    sentence = random.choice(random_sentences[language])
    return JsonResponse({'sentence': sentence})
