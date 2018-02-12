import pytest


def pytest_addoption(parser):
    parser.addoption("--runperf",
                     action="store_true",
                     help="run performance tests")
