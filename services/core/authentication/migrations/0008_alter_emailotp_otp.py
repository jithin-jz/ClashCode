from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0007_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailotp",
            name="otp",
            field=models.CharField(max_length=128),
        ),
    ]
