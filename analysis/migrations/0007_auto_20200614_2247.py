# Generated by Django 2.2.3 on 2020-06-14 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0006_auto_20200522_2340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='rating_sum',
            field=models.FloatField(default=0, verbose_name='rating sum'),
        ),
    ]