from django.db import migrations


def seed(apps, schema_editor):
    Promo = apps.get_model('orders', 'PromoCodeModel')
    for code, pct, desc in (
    ('SHEF15', 15, "Namuna promokod — 15% chegirma"),
    ('AKROMXOJA20', 20, "Namuna promokod — 20% chegirma"),
):
        Promo.objects.get_or_create(code=code, defaults={
            'description': desc, 'discount_type': 'percent', 'value': pct, 'once_per_user': True, 'is_active': False,
        })


def unseed(apps, schema_editor):
    apps.get_model('orders', 'PromoCodeModel').objects.filter(code__in=['SHEF15', 'AKROMXOJA20'], used_count=0).delete()


class Migration(migrations.Migration):
    dependencies = [('orders', '0012_promo_formats_bundle')]
    operations = [migrations.RunPython(seed, unseed)]
