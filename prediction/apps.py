import os
import sys

from django.apps import AppConfig


class PredictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prediction'

    def ready(self):
        if self._should_skip_model_init():
            return
        from .model_loader import initialize_prediction_model

        initialize_prediction_model()

    @staticmethod
    def _should_skip_model_init() -> bool:
        argv = set(sys.argv)
        management_commands = {
            'migrate', 'makemigrations', 'collectstatic', 'test',
            'shell', 'createsuperuser', 'ensure_model',
        }
        if argv & management_commands:
            return True
        if os.environ.get('SKIP_MODEL_INIT') == '1':
            return True
        return False
