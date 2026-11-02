from django.db import migrations


BRANDS = [
    ('Mercedes-Benz', 'mercedes-benz'),
    ('Audi', 'audi'),
    ('BMW', 'bmw'),
    ('Porsche', 'porsche'),
]

CATEGORIES = [
    ('Engines', 'engines'),
    ('Wheels', 'wheels'),
    ('Rims', 'rims'),
    ('Brake pads', 'brake-pads'),
]


def create_catalogue_choices(apps, schema_editor):
    database = schema_editor.connection.alias
    Brand = apps.get_model('catalog', 'Brand')
    Category = apps.get_model('catalog', 'Category')

    for name, slug in BRANDS:
        Brand.objects.using(database).get_or_create(name=name, defaults={'slug': slug})
    for name, slug in CATEGORIES:
        Category.objects.using(database).get_or_create(name=name, defaults={'slug': slug})


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_catalogue_choices, migrations.RunPython.noop),
    ]
