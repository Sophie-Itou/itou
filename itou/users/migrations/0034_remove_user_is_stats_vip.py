# Generated by Django 3.2.7 on 2021-09-30 13:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0033_alter_jobseekerprofile_hexa_non_std_extension"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="is_stats_vip",
        ),
    ]