# Generated by Django 2.2.6 on 2020-03-28 20:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0005_auto_20200323_1822'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='price_per_trip',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, help_text="Precio sugerido: 2 pasajes de Fonobus <a target='_blank' href='https://shop.ticketonline.com.ar/trips/oneway/type/1/f/352/t/559/d/2020-03-28/iR/1/c/2020-03-28/p/1/l/es'>(ver acá)</a>.", max_digits=5),
        ),
        migrations.AlterField(
            model_name='trip',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trips', to='trips.Report'),
        ),
    ]