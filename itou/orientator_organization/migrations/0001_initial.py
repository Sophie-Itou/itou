# Generated by Django 2.2.3 on 2019-07-22 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrientatorOrganization',
            fields=[
                ('siret', models.CharField(max_length=14, primary_key=True, serialize=False, verbose_name='Siret')),
                ('name', models.CharField(max_length=256, verbose_name='Nom')),
                ('address', models.CharField(max_length=256, verbose_name='Adresse')),
                ('phone', models.CharField(max_length=14, verbose_name='Téléphone')),
                ('email', models.EmailField(max_length=254, verbose_name='E-mail')),
            ],
            options={
                'verbose_name': "Structure d'accompagnement",
                'verbose_name_plural': "Structures d'accompagnement",
            },
        ),
    ]
