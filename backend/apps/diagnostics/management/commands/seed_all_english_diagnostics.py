from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "RBIS 1-11-sinflari uchun PDFlarga mos barcha English placement testlarini seed qiladi"

    def handle(self, *args, **options):
        verbosity = options.get("verbosity", 1)
        self.stdout.write("1/2: 1-4-sinf English placement testlari")
        call_command("seed_primary_english_diagnostics", verbosity=verbosity)
        self.stdout.write("2/2: 5-11-sinf English placement testlari")
        call_command("seed_senior_english_full_diagnostics", verbosity=verbosity)
        self.stdout.write(self.style.SUCCESS("1-11-sinf English placement testlari tayyor."))
