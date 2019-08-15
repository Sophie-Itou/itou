from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from itou.siaes.models import Siae
from itou.utils.address.departments import DEPARTMENTS, REGIONS


class ActiveCityManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(department__in=settings.ITOU_TEST_DEPARTMENTS)


class City(models.Model):
    """
    French cities with geocoding data.
    Raw data is generated via `django-admin generate_cities`
    and then imported into DB via `django-admin import_cities`.
    """

    DEPARTMENT_CHOICES = DEPARTMENTS.items()

    name = models.CharField(verbose_name=_("Ville"), max_length=255, db_index=True)
    slug = models.SlugField(verbose_name=_("Slug"), max_length=255, unique=True)
    department = models.CharField(verbose_name=_("Département"), choices=DEPARTMENT_CHOICES, max_length=3)
    post_codes = ArrayField(models.CharField(max_length=5), verbose_name=_("Codes postaux"), blank=True)
    code_insee = models.CharField(verbose_name=_("Code INSEE"), max_length=5, unique=True)
    # Latitude and longitude coordinates.
    # https://docs.djangoproject.com/en/2.2/ref/contrib/gis/model-api/#pointfield
    coords = gis_models.PointField(geography=True, blank=True, null=True)

    objects = models.Manager()  # The default manager.
    active_objects = ActiveCityManager()

    class Meta:
        verbose_name = _("Ville française")
        verbose_name_plural = _("Villes françaises")

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return f"{self.name} ({self.department})"

    @property
    def latitude(self):
        if self.coords:
            return self.coords.y
        return None

    @property
    def longitude(self):
        if self.coords:
            return self.coords.x
        return None

    @property
    def region(self):
        if self.department:
            for region, departments in REGIONS.items():
                if self.department in departments:
                    return region
        return None


def find_suspicious_siae_cities():
    """
    Find Siae() objects with a city name that does not exist in City().

    This could mean that:
        - the data in Siae() is wrong or too recent
        - the data in City() is wrong or not up to date

    For example, "Herblay-sur-Seine - 95" or "Saint-Père-Marc-en-Poulet - 35"
    are too recent to exist in City().

    Since data can be out of sync between Siae() and City(), there is no
    foreign key between them.
    """
    siaes = Siae.objects.order_by('city').distinct('city')
    for siae in siaes:
        try:
            City.objects.get(slug=slugify(f"{siae.city}-{siae.department}"), department=siae.department)
        except:
            print('-' * 80)
            print(f"No entry in City() for SIAE {siae.siret} - {siae.name} in {siae.city} - {siae.department}")
