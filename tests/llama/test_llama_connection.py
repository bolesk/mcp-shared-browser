import pytest
from pydantic import BaseModel
from tests.utils import Agent
from tests.llama.conftest import LLAMA_BASE_URL, LLAMA_MODEL_NAME


def make_agent() -> Agent:
    return Agent(
        model=LLAMA_MODEL_NAME,
        base_url=LLAMA_BASE_URL,
    )


@pytest.mark.asyncio
async def test_llama_basic_response(llama_server):
    agent = make_agent()
    response = await agent.get_response("Reply with exactly the word: PONG")
    assert isinstance(response.output, str)
    assert len(response.output) > 0
    assert "PONG" in response.output.upper()


@pytest.mark.asyncio
async def test_llama_structured_output(llama_server):
    class City(BaseModel):
        name: str
        country: str
        population_millions: float

    agent = make_agent()
    response = await agent.get_response(
        "Return information about the city of Rome.",
        output_model=City,
    )
    assert isinstance(response.output, City)
    assert response.output.name != ""
    assert response.output.country != ""
    assert response.output.population_millions > 0
