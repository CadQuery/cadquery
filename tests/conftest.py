import pytest


def pytest_addoption(parser):
    parser.addoption("--gui", action="store_true", default=False, help="run gui tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "gui: mark gui test")


def pytest_collection_modifyitems(config, items):

    # run gui tests --gui option is proveded
    if config.getoption("--gui"):
        return

    # skip gui tests otherwise
    skip_gui = pytest.mark.skip(reason="need --gui option to run")
    for item in items:
        if "gui" in item.keywords:
            item.add_marker(skip_gui)
