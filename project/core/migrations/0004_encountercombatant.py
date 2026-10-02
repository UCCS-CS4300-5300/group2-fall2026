from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_character_delete_starteritem_enemy_player"),
    ]

    operations = [
        migrations.CreateModel(
            name="EncounterCombatant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("role", models.CharField(choices=[("player", "Player"), ("enemy", "Enemy")], max_length=12)),
                ("hit_points", models.PositiveIntegerField()),
                ("armor_class", models.PositiveIntegerField(default=10)),
                ("attack_bonus", models.IntegerField(default=0)),
                ("damage", models.CharField(default="1d6", max_length=24)),
                ("encounter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="combatants", to="core.encounter")),
            ],
            options={"ordering": ["role", "id"]},
        ),
    ]