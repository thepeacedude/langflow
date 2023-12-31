import uuid
from langflow.services.auth.utils import get_password_hash
from langflow.services.database.models.api_key.api_key import ApiKey
from langflow.services.utils import get_settings_manager
import pytest
from fastapi.testclient import TestClient
from langflow.interface.tools.constants import CUSTOM_TOOLS
from langflow.template.frontend_node.chains import TimeTravelGuideChainNode


PROMPT_REQUEST = {
    "name": "string",
    "template": "string",
    "frontend_node": {
        "template": {},
        "description": "string",
        "base_classes": ["string"],
        "name": "",
        "display_name": "",
        "documentation": "",
        "custom_fields": {},
        "output_types": [],
        "field_formatters": {
            "formatters": {"openai_api_key": {}},
            "base_formatters": {
                "kwargs": {},
                "optional": {},
                "list": {},
                "dict": {},
                "union": {},
                "multiline": {},
                "show": {},
                "password": {},
                "default": {},
                "headers": {},
                "dict_code_file": {},
                "model_fields": {
                    "MODEL_DICT": {
                        "OpenAI": [
                            "text-davinci-003",
                            "text-davinci-002",
                            "text-curie-001",
                            "text-babbage-001",
                            "text-ada-001",
                        ],
                        "ChatOpenAI": [
                            "gpt-3.5-turbo-0613",
                            "gpt-3.5-turbo",
                            "gpt-3.5-turbo-16k-0613",
                            "gpt-3.5-turbo-16k",
                            "gpt-4-0613",
                            "gpt-4-32k-0613",
                            "gpt-4",
                            "gpt-4-32k",
                        ],
                        "Anthropic": [
                            "claude-v1",
                            "claude-v1-100k",
                            "claude-instant-v1",
                            "claude-instant-v1-100k",
                            "claude-v1.3",
                            "claude-v1.3-100k",
                            "claude-v1.2",
                            "claude-v1.0",
                            "claude-instant-v1.1",
                            "claude-instant-v1.1-100k",
                            "claude-instant-v1.0",
                        ],
                        "ChatAnthropic": [
                            "claude-v1",
                            "claude-v1-100k",
                            "claude-instant-v1",
                            "claude-instant-v1-100k",
                            "claude-v1.3",
                            "claude-v1.3-100k",
                            "claude-v1.2",
                            "claude-v1.0",
                            "claude-instant-v1.1",
                            "claude-instant-v1.1-100k",
                            "claude-instant-v1.0",
                        ],
                    }
                },
            },
        },
    },
}


@pytest.fixture
def created_api_key(session, active_user):
    hashed = get_password_hash("random_key")
    api_key = ApiKey(
        name="test_api_key",
        user_id=active_user.id,
        api_key="random_key",
        hashed_api_key=hashed,
    )

    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key


def test_process_flow_invalid_api_key(client, flow, monkeypatch):
    # Mock de process_graph_cached
    def mock_process_graph_cached(*args, **kwargs):
        return {}, "session_id_mock"

    settings_manager = get_settings_manager()
    settings_manager.auth_settings.AUTO_LOGIN = False
    from langflow.api.v1 import endpoints

    monkeypatch.setattr(endpoints, "process_graph_cached", mock_process_graph_cached)

    headers = {"api-key": "invalid_api_key"}

    post_data = {
        "inputs": {"key": "value"},
        "tweaks": None,
        "clear_cache": False,
        "session_id": None,
    }

    response = client.post(f"api/v1/process/{flow.id}", headers=headers, json=post_data)

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_process_flow_invalid_id(client, monkeypatch, created_api_key):
    def mock_process_graph_cached(*args, **kwargs):
        return {}, "session_id_mock"

    from langflow.api.v1 import endpoints

    monkeypatch.setattr(endpoints, "process_graph_cached", mock_process_graph_cached)

    api_key = created_api_key.api_key
    headers = {"api-key": api_key}

    post_data = {
        "inputs": {"key": "value"},
        "tweaks": None,
        "clear_cache": False,
        "session_id": None,
    }

    invalid_id = uuid.uuid4()
    response = client.post(
        f"api/v1/process/{invalid_id}", headers=headers, json=post_data
    )

    assert response.status_code == 404
    assert f"Flow {invalid_id} not found" in response.json()["detail"]


def test_process_flow_without_autologin(client, flow, monkeypatch, created_api_key):
    # Mock de process_graph_cached
    from langflow.api.v1 import endpoints

    settings_manager = get_settings_manager()
    settings_manager.auth_settings.AUTO_LOGIN = False

    def mock_process_graph_cached(*args, **kwargs):
        return {}, "session_id_mock"

    monkeypatch.setattr(endpoints, "process_graph_cached", mock_process_graph_cached)

    api_key = created_api_key.api_key
    headers = {"api-key": api_key}

    # Dummy POST data
    post_data = {
        "inputs": {"key": "value"},
        "tweaks": None,
        "clear_cache": False,
        "session_id": None,
    }

    # Make the request to the FastAPI TestClient

    response = client.post(f"api/v1/process/{flow.id}", headers=headers, json=post_data)

    # Check the response
    assert response.status_code == 200, response.json()
    assert response.json()["result"] == {}
    assert response.json()["session_id"] == "session_id_mock"


def test_process_flow_fails_autologin_off(client, flow, monkeypatch):
    # Mock de process_graph_cached
    from langflow.api.v1 import endpoints

    settings_manager = get_settings_manager()
    settings_manager.auth_settings.AUTO_LOGIN = False

    def mock_process_graph_cached(*args, **kwargs):
        return {}, "session_id_mock"

    monkeypatch.setattr(endpoints, "process_graph_cached", mock_process_graph_cached)

    headers = {"api-key": "api_key"}

    # Dummy POST data
    post_data = {
        "inputs": {"key": "value"},
        "tweaks": None,
        "clear_cache": False,
        "session_id": None,
    }

    # Make the request to the FastAPI TestClient

    response = client.post(f"api/v1/process/{flow.id}", headers=headers, json=post_data)

    # Check the response
    assert response.status_code == 403, response.json()
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_get_all(client: TestClient, logged_in_headers):
    response = client.get("api/v1/all", headers=logged_in_headers)
    assert response.status_code == 200
    json_response = response.json()
    # We need to test the custom nodes
    assert "PromptTemplate" in json_response["prompts"]
    # All CUSTOM_TOOLS(dict) should be in the response
    assert all(tool in json_response["tools"] for tool in CUSTOM_TOOLS.keys())


def test_post_validate_code(client: TestClient):
    # Test case with a valid import and function
    code1 = """
import math

def square(x):
    return x ** 2
"""
    response1 = client.post("api/v1/validate/code", json={"code": code1})
    assert response1.status_code == 200
    assert response1.json() == {"imports": {"errors": []}, "function": {"errors": []}}

    # Test case with an invalid import and valid function
    code2 = """
import non_existent_module

def square(x):
    return x ** 2
"""
    response2 = client.post("api/v1/validate/code", json={"code": code2})
    assert response2.status_code == 200
    assert response2.json() == {
        "imports": {"errors": ["No module named 'non_existent_module'"]},
        "function": {"errors": []},
    }

    # Test case with a valid import and invalid function syntax
    code3 = """
import math

def square(x)
    return x ** 2
"""
    response3 = client.post("api/v1/validate/code", json={"code": code3})
    assert response3.status_code == 200
    assert response3.json() == {
        "imports": {"errors": []},
        "function": {"errors": ["expected ':' (<unknown>, line 4)"]},
    }

    # Test case with invalid JSON payload
    response4 = client.post("api/v1/validate/code", json={"invalid_key": code1})
    assert response4.status_code == 422

    # Test case with an empty code string
    response5 = client.post("api/v1/validate/code", json={"code": ""})
    assert response5.status_code == 200
    assert response5.json() == {"imports": {"errors": []}, "function": {"errors": []}}

    # Test case with a syntax error in the code
    code6 = """
import math

def square(x)
    return x ** 2
"""
    response6 = client.post("api/v1/validate/code", json={"code": code6})
    assert response6.status_code == 200
    assert response6.json() == {
        "imports": {"errors": []},
        "function": {"errors": ["expected ':' (<unknown>, line 4)"]},
    }


VALID_PROMPT = """
I want you to act as a naming consultant for new companies.

Here are some examples of good company names:

- search engine, Google
- social media, Facebook
- video sharing, YouTube

The name should be short, catchy and easy to remember.

What is a good name for a company that makes {product}?
"""

INVALID_PROMPT = "This is an invalid prompt without any input variable."


def test_valid_prompt(client: TestClient):
    PROMPT_REQUEST["template"] = VALID_PROMPT
    response = client.post("api/v1/validate/prompt", json=PROMPT_REQUEST)
    assert response.status_code == 200
    assert response.json()["input_variables"] == ["product"]


def test_invalid_prompt(client: TestClient):
    PROMPT_REQUEST["template"] = INVALID_PROMPT
    response = client.post(
        "api/v1/validate/prompt",
        json=PROMPT_REQUEST,
    )
    assert response.status_code == 200
    assert response.json()["input_variables"] == []


@pytest.mark.parametrize(
    "prompt,expected_input_variables",
    [
        ("{color} is my favorite color.", ["color"]),
        ("The weather is {weather} today.", ["weather"]),
        ("This prompt has no variables.", []),
        ("{a}, {b}, and {c} are variables.", ["a", "b", "c"]),
    ],
)
def test_various_prompts(client, prompt, expected_input_variables):
    TimeTravelGuideChainNode().to_dict()
    PROMPT_REQUEST["template"] = prompt
    response = client.post("api/v1/validate/prompt", json=PROMPT_REQUEST)
    assert response.status_code == 200
    assert response.json()["input_variables"] == expected_input_variables
