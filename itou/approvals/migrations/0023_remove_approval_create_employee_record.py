# Generated by Django 3.2.8 on 2021-12-16 15:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("approvals", "0022_alter_approval_create_employee_record"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="approval",
            name="create_employee_record",
        ),
    ]