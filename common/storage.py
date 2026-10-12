from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_storage():
    """Pullik raqamli fayllar (e-kitob, to'liq audio) uchun yopiq saqlash joyi — URL orqali ochiq emas."""
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)
