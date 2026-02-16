from src.config import get_settings


def test_initial_config_file():
    settings = get_settings()

    print("Database URL:", settings.database_url)
    print("Debug:", settings.debug)
    print("Storage Backend:", settings.storage_backend)
