# Generated by Django 4.2.16 on 2025-06-26 03:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('admin', 'Administrator'), ('staff', 'Staff'), ('enumerator', 'Enumerator'), ('respondent', 'Respondent')], max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('multiple_choice', 'Multiple Choice'), ('multiple_select', 'Multiple Select'), ('text', 'Text'), ('rating', 'Rating')], default='text', max_length=50),
        ),
        migrations.AlterField(
            model_name='survey',
            name='status',
            field=models.IntegerField(default=0, help_text='Set to Zero (0) to stop accepting responses.', verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='survey.userrole'),
        ),
    ]
