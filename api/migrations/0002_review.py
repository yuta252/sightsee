# Generated by Django 2.2.3 on 2019-11-11 08:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lang', models.CharField(default='NA', max_length=5, verbose_name='language')),
                ('review_post', models.TextField(blank=True, help_text='Please enter within 140 characters.', max_length=140, null=True, verbose_name='review')),
                ('review_rating', models.FloatField(blank=True, null=True, verbose_name='rating')),
                ('date_posted', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date posted')),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='review_writer', to='api.AppUser')),
                ('spotId', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='review_target', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'review',
                'ordering': ('-date_posted',),
            },
        ),
    ]