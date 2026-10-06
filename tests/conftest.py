import asyncio
import inspect
import pytest
from langchain_core.messages import AIMessage

from lab.testing import ScriptedChatModel


@pytest.fixture
def scripted():
    """Factory: scripted(*messages) -> ScriptedChatModel that replays the given AIMessages."""
    def make(*messages):
        return ScriptedChatModel(script=list(messages) or [AIMessage(content="done")])
    return make


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test to run asynchronously")


def pytest_pyfunc_call(pyfuncitem):
    if inspect.iscoroutinefunction(pyfuncitem.obj):
        args = {arg: pyfuncitem.funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}
        asyncio.run(pyfuncitem.obj(**args))
        return True
