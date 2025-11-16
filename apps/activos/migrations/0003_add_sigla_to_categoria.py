# Generated manually to add sigla field with data migration

from django.db import migrations, models


def populate_siglas(apps, schema_editor):
    """
    Pobla el campo sigla con valores únicos basados en los códigos existentes.
    Si el código tiene 3 o más caracteres, usa los primeros 3.
    Si no, genera un código único basado en el ID.
    """
    CategoriaActivo = apps.get_model('activos', 'CategoriaActivo')

    for idx, categoria in enumerate(CategoriaActivo.objects.all(), start=1):
        if len(categoria.codigo) >= 3:
            # Usar los primeros 3 caracteres del código
            sigla = categoria.codigo[:3].upper()
        else:
            # Generar sigla basada en código más padding
            sigla = (categoria.codigo + 'XX')[:3].upper()

        # Asegurar unicidad
        base_sigla = sigla
        counter = 1
        while CategoriaActivo.objects.filter(sigla=sigla).exists():
            sigla = f"{base_sigla[:2]}{counter}"
            counter += 1

        categoria.sigla = sigla
        categoria.save()


class Migration(migrations.Migration):

    dependencies = [
        ('activos', '0002_initial'),
    ]

    operations = [
        # 1. Añadir campo sigla sin restricción unique y nullable
        migrations.AddField(
            model_name='categoriaactivo',
            name='sigla',
            field=models.CharField(
                max_length=3,
                null=True,
                blank=True,
                verbose_name='Sigla',
                help_text='Sigla de 3 caracteres para generación automática de códigos de activos (ej: NTB, LCD, ESC)'
            ),
        ),
        # 2. Poblar el campo con datos
        migrations.RunPython(populate_siglas, reverse_code=migrations.RunPython.noop),
        # 3. Hacer el campo unique y not null
        migrations.AlterField(
            model_name='categoriaactivo',
            name='sigla',
            field=models.CharField(
                max_length=3,
                unique=True,
                verbose_name='Sigla',
                help_text='Sigla de 3 caracteres para generación automática de códigos de activos (ej: NTB, LCD, ESC)'
            ),
        ),
    ]
