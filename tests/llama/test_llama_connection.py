import pytest
from pydantic import BaseModel
from tests.utils import BrowserAgent
from tests.llama.conftest import LLAMA_BASE_URL, LLAMA_MODEL_NAME


def make_agent() -> BrowserAgent:
    return BrowserAgent(
        model=LLAMA_MODEL_NAME,
        base_url=LLAMA_BASE_URL,
    )


@pytest.mark.asyncio
async def test_llama_basic_response(llama_server):
    agent = make_agent()
    result = await agent.get_response("Reply with exactly the word: PONG")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "PONG" in result.upper()


@pytest.mark.asyncio
async def test_llama_structured_output(llama_server):
    class City(BaseModel):
        name: str
        country: str
        population_millions: float

    agent = make_agent()
    result = await agent.get_response(
        "Return information about the city of Rome.",
        output_model=City,
    )
    assert isinstance(result, City)
    assert result.name != ""
    assert result.country != ""
    assert result.population_millions > 0
