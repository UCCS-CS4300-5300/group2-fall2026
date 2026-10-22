import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_characterencounter_x_pos_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Quest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=500)),
                ("completed", models.BooleanField(default=False)),
                ("encounter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quests", to="core.encounter")),
            ],
        ),
    ]
