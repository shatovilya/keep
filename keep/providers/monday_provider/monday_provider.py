"""
MondayProvider is a class that provides a way to create new pulse on Monday.com.
"""

import dataclasses
import json

import pydantic
import requests

from keep.api.core.config import config
from keep.contextmanager.contextmanager import ContextManager
from keep.exceptions.provider_exception import ProviderException
from keep.providers.base.base_provider import BaseProvider
from keep.providers.models.provider_config import ProviderConfig, ProviderScope


@pydantic.dataclasses.dataclass
class MondayProviderAuthConfig:
    """
    MondayProviderAuthConfig is a class that holds the authentication information for the MondayProvider.
    """

    api_token: str = dataclasses.field(
        metadata={
            "required": False,
            "description": "Personal API Token",
            "sensitive": True,
        },
        default="",
    )
    access_token: str = dataclasses.field(
        metadata={
            "description": "For access token installation flow, use Keep UI",
            "required": False,
            "sensitive": True,
            "hidden": True,
        },
        default="",
    )
    scopes: str = dataclasses.field(
        metadata={
            "description": "Scopes from OAuth logic, comma separated",
            "required": False,
            "sensitive": False,
            "hidden": True,
        },
        default="",
    )


class MondayProvider(BaseProvider):
    PROVIDER_DISPLAY_NAME = "Monday"
    PROVIDER_CATEGORY = ["Collaboration", "Organizational Tools"]
    OAUTH2_URL = config("MONDAY_OAUTH2_URL", default=None)
    MONDAY_CLIENT_ID = config("MONDAY_CLIENT_ID", default=None)
    MONDAY_CLIENT_SECRET = config("MONDAY_CLIENT_SECRET", default=None)
    PROVIDER_SCOPES = [
        ProviderScope(
            name="create_pulse",
            description="Create a new pulse",
        ),
    ]

    PROVIDER_TAGS = ["ticketing"]

    url = "https://api.monday.com/v2"

    def __init__(
        self, context_manager: ContextManager, provider_id: str, config: ProviderConfig
    ):
        super().__init__(context_manager, provider_id, config)

    def dispose(self):
        pass

    def validate_config(self):
        self.authentication_config = MondayProviderAuthConfig(
            **self.config.authentication
        )
        if (
            not self.authentication_config.access_token
            and not self.authentication_config.api_token
        ):
            raise ProviderException("API token or access token is required")

    def validate_scopes(self) -> dict[str, bool | str]:
        """
        Validate scopes for the provider
        """
        try:
            response = requests.post(
                self.url,
                json={"query": "query { me { id } }"},
                headers=self._get_auth_headers(),
            )

            if response.status_code != 200:
                response.raise_for_status()

            self.logger.info(f"Successfully validated scopes {response.json()}")

            return {"create_pulse": True}

        except Exception as e:
            self.logger.exception("Failed to validate scopes", extra={"error": e})
            return {"create_pulse": str(e)}

    @staticmethod
    def oauth2_logic(**payload) -> dict:
        """
        Handle the OAuth2 flow for the Monday provider
        """
        request = requests.post(
            "https://auth.monday.com/oauth2/token",
            json={
                "client_id": MondayProvider.MONDAY_CLIENT_ID,
                "client_secret": MondayProvider.MONDAY_CLIENT_SECRET,
                "code": payload.get("code"),
                "redirect_uri": payload.get("redirect_uri"),
            },
        )
        request.raise_for_status()
        response = request.json()
        new_provider_info = {
            "access_token": response.get("access_token"),
            "scopes": response.get("scope"),
        }
        return new_provider_info

    def _get_auth_headers(self):
        """
        Get the authentication headers
        """
        if self.authentication_config.access_token:
            return {
                "Authorization": f"Bearer {self.authentication_config.access_token}",
            }
        else:
            return {
                "Authorization": self.authentication_config.api_token,
            }

    def _create_new_pulse(
        self,
        board_id: int,
        group_id: str,
        item_name: str,
        column_values: dict = None,
    ):
        try:
            self.logger.info("Creating new item")
            headers = self._get_auth_headers()

            query = """
            mutation ($board_id: ID!, $group_id: String!, $item_name: String!, $column_values: JSON) {
                create_item(board_id: $board_id, group_id: $group_id, item_name: $item_name, column_values: $column_values) {
                    id
                }
            }
            """

            if column_values is None:
                column_values = {}

            column_values = json.dumps(
                {k: v for d in column_values for k, v in d.items()}
            )

            variables = {
                "board_id": board_id,
                "group_id": group_id,
                "item_name": item_name,
                "column_values": column_values,
            }

            response = requests.post(
                self.url, json={"query": query, "variables": variables}, headers=headers
            )

            self.logger.info("Response received", extra={"resp": response.json()})
            self.logger.info(f"Status Code: {response.status_code}")

            try:
                if response.status_code != 200:
                    response.raise_for_status()
                self.logger.info("Item created successfully")
                return response.json()

            except Exception:
                self.logger.exception(
                    "Failed to create item", extra={"resp": response.json()}
                )
                raise ProviderException(f"Failed to create item: {response.json()}")

        except Exception as e:
            raise ProviderException(f"Failed to create item: {e}")

    def _notify(
        self,
        board_id: int,
        group_id: str,
        item_name: str,
        column_values: dict = None,
    ):
        try:
            self.logger.info("Creating new item")
            self._create_new_pulse(board_id, group_id, item_name, column_values)
            self.logger.info("Item created successfully")
        except Exception as e:
            raise ProviderException(f"Failed to create item: {e}")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
    context_manager = ContextManager(
        tenant_id="singletenant",
        workflow_id="test",
    )

    import os

    api_token = os.environ.get("API_TOKEN")

    if api_token is None:
        raise Exception("API_TOKEN is required")

    config = ProviderConfig(
        description="Monday Provider",
        authentication={
            "api_token": api_token,
        },
    )

    monday_provider = MondayProvider(
        context_manager=context_manager,
        provider_id="monday_provider",
        config=config,
    )

    board_id = 1956384489
    group_id = "topics"
    item_name = "New Item"

    column_values = [{"text_mkm77x3p": "helo"}, {"text_1_mkm7x2ep": "10"}]

    monday_provider._notify(board_id, group_id, item_name, column_values)
