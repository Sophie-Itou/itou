# Generated by Django 3.2.4 on 2021-06-23 07:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eligibility", "0005_auto_20200913_0532"),
        ("job_applications", "0033_alter_jobapplication_created_from_pe_approval"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="eligibility_diagnosis",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="eligibility.eligibilitydiagnosis",
                verbose_name="Diagnostic d'éligibilité",
            ),
        ),
    ]