# Generated by Django 3.2.7 on 2021-10-16 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0034_remove_user_is_stats_vip"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobseekerprofile",
            name="hexa_additional_address",
            field=models.CharField(blank=True, max_length=32, verbose_name="Complément d'adresse"),
        ),
    ]