from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from desercion_escolar.quality import normalize_email


class CustomUser(AbstractUser):
    nombre = models.CharField(max_length=100, default='Desconocido')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='uniq_customuser_email_ci',
                condition=~Q(email=''),
            ),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = normalize_email(self.email)
        super().save(*args, **kwargs)
