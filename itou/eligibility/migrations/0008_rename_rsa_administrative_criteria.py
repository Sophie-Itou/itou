# Generated by Django 3.2.5 on 2021-09-17 17:24

from django.db import migrations


def migrate_data_forward(apps, schema_editor):  # pylint: disable=unused-argument
    AdministrativeCriteria = apps.get_model("eligibility", "AdministrativeCriteria")
    AdministrativeCriteria.objects.filter(name="Bénéficiaire du RSA (socle)").update(name="Bénéficiaire du RSA")


def migrate_data_backward(apps, schema_editor):  # pylint: disable=unused-argument
    AdministrativeCriteria = apps.get_model("eligibility", "AdministrativeCriteria")
    AdministrativeCriteria.objects.filter(name="Bénéficiaire du RSA").update(name="Bénéficiaire du RSA (socle)")


class Migration(migrations.Migration):

    dependencies = [
        ("eligibility", "0007_administrativecriteria_written_proof_validity"),
    ]

    operations = [migrations.RunPython(migrate_data_forward, migrate_data_backward)]