# Generated by Django 2.2.6 on 2019-10-23 09:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("job_applications", "0005_auto_20191017_0723")]

    operations = [migrations.RemoveField(model_name="jobapplication", name="siae")]
