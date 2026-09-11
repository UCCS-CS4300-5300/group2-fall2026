from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="StudySession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("topic", models.CharField(max_length=150)),
                ("duration_minutes", models.IntegerField()),
                ("completed_on", models.DateField(auto_now_add=True)),
            ],
        ),
    ]
