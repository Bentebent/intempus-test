from config import Config
import pytest
import dotenv

@pytest.fixture(scope='session', autouse=True)
def get_config(request) -> Config:
    if not dotenv.load_dotenv(r".\.dev\.env.test"):
        print("No environment variables read from env var file")
    return Config()  # ty:ignore[missing-argument]
    