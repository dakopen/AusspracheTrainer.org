# Generated by Django 4.1.10 on 2023-12-09 11:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyze', '0004_phonemeassessmentresult_how_many_times_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pronunciationassessmentresult',
            name='word_assessment',
        ),
    ]
