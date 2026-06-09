import json
from pathlib import Path

from django.core.management.base import BaseCommand

from web_app.models import Province, Municipality


class Command(BaseCommand):
    help = "Loads provinces and municipalities from a JSON file into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default=None,
            help='Path to the JSON data file. Defaults to data/municipalities_spain.json',
        )

    def handle(self, *args, **options):
        source = options.get('source')
        if not source:
            source = Path(__file__).resolve().parents[3] / 'data' / 'municipalities_spain.json'

        source_path = Path(source)

        if not source_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {source_path}"))
            return

        with open(source_path, encoding='utf-8') as f:
            data = json.load(f)

        provinces_created = 0
        municipalities_created = 0

        for province_data in data:
            province, created = Province.objects.update_or_create(
                ine_code=province_data['ine_code'],
                defaults={'name': province_data['name']},
            )
            if created:
                provinces_created += 1
                self.stdout.write(f"  Created province: {province.name}")

            for municipality_data in province_data.get('municipalities', []):
                municipality, created = Municipality.objects.update_or_create(
                    ine_code=municipality_data['ine_code'],
                    defaults={
                        'name': municipality_data['name'],
                        'province': province,
                    },
                )
                if created:
                    municipalities_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. {provinces_created} provinces and {municipalities_created} municipalities loaded."
        ))
