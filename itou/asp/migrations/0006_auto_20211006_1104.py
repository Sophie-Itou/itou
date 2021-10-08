# Generated by Django 3.2.7 on 2021-10-06 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asp", "0005_alters_for_employee_record_ui"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commune",
            name="end_date",
            field=models.DateField(blank=True, null=True, verbose_name="Fin de validité"),
        ),
        migrations.AlterField(
            model_name="department",
            name="end_date",
            field=models.DateField(blank=True, null=True, verbose_name="Fin de validité"),
        ),
    ]