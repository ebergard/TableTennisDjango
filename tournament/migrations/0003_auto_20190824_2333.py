# Generated by Django 2.1.7 on 2019-08-24 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0002_remove_tournament_participants'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='participant1',
        ),
        migrations.RemoveField(
            model_name='game',
            name='participant2',
        ),
    ]
