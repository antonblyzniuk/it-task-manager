from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_project_members"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectmembership",
            name="position",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="memberships",
                to="main.position",
            ),
        ),
        migrations.RemoveField(
            model_name="worker",
            name="position",
        ),
    ]
