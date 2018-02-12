import pytest
import logging


@pytest.fixture
def analysisLog():
    logging.basicConfig()
    logger = logging.getLogger('dualpriority.analysis')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def eqLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.utils.eq')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def runnerLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.runner')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def simulatorLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.internals.simulator')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def simLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.sim')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def histLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.hist')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def schedLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.internals.sched')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def statsLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.stats')
    logger.setLevel(logging.DEBUG)
    yield logger
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def genLog():
    logging.basicConfig()
    logger = logging.getLogger('crpd.gen')
    logger.setLevel(logging.DEBUG)
    yield None
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def testLog():
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    yield logger
    logger.setLevel(logging.NOTSET)
