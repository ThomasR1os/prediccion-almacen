import os
import sys

from django.apps import AppConfig


class PredictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prediction'

    def ready(self):
        if self._should_skip_model_init():
            return

        from django.conf import settings

        from .model_storage import model_file_available

        if not model_file_available(settings.MODEL_PATH):
            print(
                "Model not on disk yet; skipping warmup "
                "(scripts/ensure_model.py runs before Gunicorn)."
            )
            return

        from .model_loader import warmup_prediction_model

        warmup_prediction_model()

    @staticmethod
    def _should_skip_model_init() -> bool:
        argv = set(sys.argv)
        management_commands = {
            'migrate', 'makemigrations', 'collectstatic', 'test',
            'shell', 'createsuperuser',
        }
        if argv & management_commands:
            return True
        if os.environ.get('SKIP_MODEL_INIT') == '1':
            return True
        return False
