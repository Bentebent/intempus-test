from config import Config
import pytest
import dotenv

@pytest.fixture(scope='session', autouse=True)
def get_config(request) -> Config:
    if not dotenv.load_dotenv(r".\.dev\.env.test"):
        print("No environment variables read from env var file")
    return Config()  # ty:ignore[missing-argument]

def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow) 