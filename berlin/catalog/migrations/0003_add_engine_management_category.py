from django.db import migrations


def add_engine_management_category(apps, schema_editor):
    database = schema_editor.connection.alias
    Category = apps.get_model('catalog', 'Category')
    Category.objects.using(database).get_or_create(
        name='Engine management and control units',
        defaults={'slug': 'engine-management-and-control-units'},
    )


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0002_seed_catalogue_choices'),
    ]

    operations = [
        migrations.RunPython(add_engine_management_category, migrations.RunPython.noop),
    ]
