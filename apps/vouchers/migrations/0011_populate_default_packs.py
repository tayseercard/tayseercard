from django.db import migrations

def create_default_packs(apps, schema_editor):
    VoucherPrice = apps.get_model('vouchers', 'VoucherPrice')
    
    defaults = [
        {
            'title': 'Starter',
            'value': 15.0,
            'price': 1500.0,
            'pack_quantity': 100,
            'description': '',
            'is_active': True,
        },
        {
            'title': 'Standard',
            'value': 10.0,
            'price': 3000.0,
            'pack_quantity': 300,
            'description': '',
            'is_active': True,
        },
        {
            'title': 'Premium',
            'value': 7.0,
            'price': 4900.0,
            'pack_quantity': 7000,
            'description': '',
            'is_active': True,
        }
    ]
    
    for item in defaults:
        VoucherPrice.objects.get_or_create(
            title=item['title'],
            defaults=item
        )

def remove_default_packs(apps, schema_editor):
    VoucherPrice = apps.get_model('vouchers', 'VoucherPrice')
    VoucherPrice.objects.filter(title__in=['Starter', 'Standard', 'Premium']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('vouchers', '0010_voucher_updated_by_alter_voucher_status'),
    ]

    operations = [
        migrations.RunPython(create_default_packs, remove_default_packs),
    ]
