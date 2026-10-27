from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_character_char_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="character",
            name="strength_save_bonus",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="character",
            name="dexterity_save_bonus",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="character",
            name="constitution_save_bonus",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="character",
            name="intelligence_save_bonus",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="character",
            name="wisdom_save_bonus",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="character",
            name="charisma_save_bonus",
            field=models.IntegerField(default=0),
        ),
    ]