from django.db import models


class MemoryLog(models.Model):
    created = models.DateTimeField()
    source = models.CharField(max_length=255)
    params = models.CharField(max_length=255)
    memory = models.BigIntegerField()
    increment = models.BigIntegerField()

    class Meta:
        ordering = ['-created']
