from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from django.utils import translation
from django.template.loader import render_to_string
from analyze.tasks import async_pronunciation_assessment
from celery.result import AsyncResult
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.conf import settings
import random
import uuid
from pydub import AudioSegment
import base64
import io
import os
from analyze.models import PronunciationAssessmentResult
from analyze.text_to_speech import synthesize_speech
from frontend.languages import country_class_to_locale
from django.conf import settings
from django.urls import reverse
import logging
from django.views.decorators.http import require_POST
from django.templatetags.static import static

languages = ['en-GB', 'de-DE', 'fr-FR']
random_sentences = {lang: open(os.path.join(settings.BASE_DIR, f'frontend/random_sentences/{lang.split("-")[0]}_validated.txt'), encoding="utf-8-sig").read().splitlines() for lang in languages}  # 5000 per language

logger = logging.getLogger(__name__)


def render_into_base(request, title, filepaths, context=None, content_type=None, status=None, using=None, css=None, extra_head=None):
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

    if extra_head:
        if not isinstance(extra_head, list):
            extra_head = [extra_head]
    context["extra_head"] = extra_head

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

    extra_head = {
        "name": "description", 
        "content": _("Der kostenlose AusspracheTrainer hilft dir, deine Aussprache zu verbessern. Sprich einen Satz ein und erhalte eine Bewertung deiner Aussprache.\ndeutsch · englisch · französisch")
    }

    return render_into_base(request, _("AusspracheTrainer"), ["index.html", "tutorial.html"], context,
                            css=['frontend/assets/css/index.css', 'frontend/assets/css/tutorial.css'], extra_head=extra_head)


def legal_notice(request):

    return render_into_base(request, _("Impressum"), "legal_notice.html", css=['frontend/assets/css/legal.css'])


def privacy_policy(request):
    return render_into_base(request, _("Datenschutzerklärung"), "privacy_policy.html", css=['frontend/assets/css/legal.css'])

def about_page(request):
    return render_into_base(request, _("Über uns"), "about.html", css=['frontend/assets/css/legal.css'])


def initiate_analysis(request):
    audio_data_url = request.POST.get('audio_data')
    text = request.POST.get('text_data')
    selected_language = request.POST.get('selected_language')   
    audio_mimetype = request.POST.get('audio_mimetype')
    logger.warn(f"Initiating analysis for {selected_language} with mimetype {audio_mimetype}")
    audio_data_base64 = audio_data_url.split(',')[1]
    audio_data = base64.b64decode(audio_data_base64)



    buffer = io.BytesIO()
    if audio_mimetype == "audio/ogg":
        audio_segment = AudioSegment.from_ogg(io.BytesIO(audio_data))
    elif audio_mimetype == "audio/wav":
        audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
    elif audio_mimetype == "audio/mp4":
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp4")
    elif audio_mimetype == "audio/mpeg":
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
    elif audio_mimetype == "audio/webm":
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
    else:
        return JsonResponse({'error': 'Unsupported audio format'})

    if len(audio_segment) > 59000:
        audio_segment = audio_segment[:59000]  # max. 59 seconds
    audio_segment.export(buffer, format="wav")

    buffer.seek(0)

    content_file = ContentFile(buffer.read())
    
    # Save audio file to disk
    random_name = str(uuid.uuid4()) + ".wav"
    file_name = 'audio_files/' + random_name
    settings.SECURE_FILE_STORAGE.save(file_name, content_file)
    file_name = 'secure_storage/' + file_name
    logger.warn(f"Saved audio file to {file_name}")
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

def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        # Add other rules here
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def text_to_speech(request):
        
    # Extract metadata from request
    text = request.GET.get('text')
    language = request.GET.get('language')


    if not text or not language:
        return JsonResponse({'error': 'No text/language provided'}, status=400)


    filepath = synthesize_speech(text, language)

    if filepath:
        # Provide a URL to access the audio file
        audio_url = request.build_absolute_uri(settings.MEDIA_URL + filepath)
        # audio_url starts with http://, but we want https://
        audio_url = "https://" + audio_url[7:]
        return JsonResponse({'audio_url': audio_url})


