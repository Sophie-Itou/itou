# Generated by Django 3.1.2 on 2020-10-06 15:55

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import itou.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("siaes", "0035_auto_20200924_1420"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiaeConvention",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("EI", "Entreprise d'insertion"),
                            ("AI", "Association intermédiaire"),
                            ("ACI", "Atelier chantier d'insertion"),
                            ("ETTI", "Entreprise de travail temporaire d'insertion"),
                            ("EITI", "Entreprise d'insertion par le travail indépendant"),
                        ],
                        default="EI",
                        max_length=4,
                        verbose_name="Type",
                    ),
                ),
                (
                    "siret_signature",
                    models.CharField(
                        db_index=True,
                        max_length=14,
                        validators=[itou.utils.validators.validate_siret],
                        verbose_name="Siret à la signature de la convention",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text=(
                            "Précise si la convention est active c.a.d. si elle "
                            "a au moins une annexe financière valide à ce jour."
                        ),
                        verbose_name="Active",
                    ),
                ),
                (
                    "deactivated_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name="Date de  désactivation et début de délai de grâce",
                    ),
                ),
                (
                    "reactivated_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Date de réactivation manuelle"),
                ),
                ("asp_id", models.IntegerField(db_index=True, verbose_name="ID ASP de la SIAE")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de modification")),
                (
                    "reactivated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reactivated_siae_convention_set",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Réactivée manuellement par",
                    ),
                ),
            ],
            options={
                "verbose_name": "Convention",
                "verbose_name_plural": "Conventions",
                "unique_together": {("asp_id", "kind")},
            },
        ),
        migrations.AlterField(
            model_name="siae",
            name="source",
            field=models.CharField(
                choices=[
                    ("ASP", "Export ASP"),
                    ("GEIQ", "Export GEIQ"),
                    ("USER_CREATED", "Utilisateur (Antenne)"),
                    ("STAFF_CREATED", "Staff Itou"),
                ],
                default="ASP",
                max_length=20,
                verbose_name="Source de données",
            ),
        ),
        migrations.CreateModel(
            name="SiaeFinancialAnnex",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "number",
                    models.CharField(
                        db_index=True,
                        max_length=17,
                        unique=True,
                        validators=[itou.utils.validators.validate_af_number],
                        verbose_name="Numéro d'annexe financière",
                    ),
                ),
                (
                    "convention_number",
                    models.CharField(
                        db_index=True,
                        max_length=19,
                        verbose_name="Numéro de convention",
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("VALIDE", "Valide"),
                            ("PROVISOIRE", "Provisoire (valide)"),
                            ("HISTORISE", "Archivé (invalide)"),
                            ("ANNULE", "Annulé"),
                            ("SAISI", "Saisi (invalide)"),
                            ("BROUILLON", "Brouillon (invalide)"),
                            ("CLOTURE", "Cloturé (invalide)"),
                            ("REJETE", "Rejeté"),
                        ],
                        max_length=20,
                        verbose_name="Etat",
                    ),
                ),
                ("start_at", models.DateTimeField(verbose_name="Date de début d'effet")),
                ("end_at", models.DateTimeField(verbose_name="Date de fin d'effet")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de modification")),
                (
                    "convention",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="financial_annexes",
                        to="siaes.siaeconvention",
                    ),
                ),
            ],
            options={"verbose_name": "Annexe financière", "verbose_name_plural": "Annexes financières"},
        ),
        migrations.AddField(
            model_name="siae",
            name="convention",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="siaes",
                to="siaes.siaeconvention",
            ),
        ),
    ]
