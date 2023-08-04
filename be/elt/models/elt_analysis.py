from django.contrib.gis.db import models

from elt.lib.types import EltAnalysisEnum, Juri
from elt.models.model_utils import SanitizedRawModelMixin


class EltAnalysis(SanitizedRawModelMixin, models.Model):
    class Meta:
        verbose_name = "ELT Analysis"
        verbose_name_plural = "ELT Analyses"

    juri = models.CharField(choices=[(x.value, x.name) for x in Juri], max_length=20)
    analysis = models.CharField(choices=[(x.value, x.name) for x in EltAnalysisEnum], max_length=20)
    run_date = models.DateField()
    # TODO: for multi-jurisdiction we will want to use a standardized Parcel table..
    parcels = models.ManyToManyField("RawSfParcelWrap")
