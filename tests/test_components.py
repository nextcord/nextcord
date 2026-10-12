import pydantic
import pytest

import nextcord
from nextcord.types import components as comp_payloads
from nextcord.utils import MISSING
from tests import utils


def test_base():
    assert True


def test_base_component_payload():
    ta = pydantic.TypeAdapter(comp_payloads.BaseComponent)
    ta.validate_python({"type": 1, "id": 1}, extra="forbid")


class TestActionRowAndButtons:
    @pytest.fixture(scope="class")
    def comps(self) -> list[nextcord.Component]:
        return [
            nextcord.ActionRow(
                [
                    nextcord.Button.as_primary(
                        label="Primary1", component_id=11, custom_id="test_button_11"
                    ),  # Test basic label.
                    nextcord.Button.as_primary(
                        emoji="⚠️", component_id=12, custom_id="test_button_12"
                    ),  # Test basic string emoji.
                    nextcord.Button.as_primary(
                        label="Primary3", emoji="⚠️", component_id=13, custom_id="test_button_13"
                    ),  # Test label + emoji.
                    nextcord.Button.as_primary(
                        label="Primary4", disabled=True, component_id=14, custom_id="test_button_14"
                    ),  # Test Disabled = True.
                    nextcord.Button.as_primary(
                        label="Primary5",
                        disabled=False,
                        component_id=15,
                        custom_id="test_button_15",
                    ),  # Test Disabled = False.
                ],
                component_id=1,
            ),
            nextcord.ActionRow(
                [
                    nextcord.Button.as_secondary(
                        label="Secondary", component_id=21, custom_id="test_button_21"
                    ),
                    nextcord.Button.as_success(
                        label="Success", component_id=22, custom_id="test_button_22"
                    ),
                    nextcord.Button.as_danger(
                        label="Danger", component_id=23, custom_id="test_button_23"
                    ),
                ],
                component_id=2,
            ),
            nextcord.ActionRow(
                [
                    nextcord.Button.as_link(
                        "https://docs.discord.com/developers/components/reference#button",
                        label="Link1",
                        component_id=31,
                    ),
                ],
                component_id=3,
            ),
        ]

    @pytest.fixture(scope="class")
    def comp_payload(self, comps):
        return [comp.to_dict() for comp in comps]

    @pytest.fixture(scope="class")
    def offline_response(self):
        return [
            {
                "type": 1,
                "id": 1,
                "components": [
                    {
                        "type": 2,
                        "id": 11,
                        "custom_id": "test_button_11",
                        "style": 1,
                        "label": "Primary1",
                    },
                    {
                        "type": 2,
                        "id": 12,
                        "custom_id": "test_button_12",
                        "style": 1,
                        "emoji": {"name": "⚠️"},
                    },
                    {
                        "type": 2,
                        "id": 13,
                        "custom_id": "test_button_13",
                        "style": 1,
                        "label": "Primary3",
                        "emoji": {"name": "⚠️"},
                    },
                    {
                        "type": 2,
                        "id": 14,
                        "custom_id": "test_button_14",
                        "style": 1,
                        "label": "Primary4",
                        "disabled": True,
                    },
                    {
                        "type": 2,
                        "id": 15,
                        "custom_id": "test_button_15",
                        "style": 1,
                        "label": "Primary5",
                    },
                ],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 2,
                        "id": 21,
                        "custom_id": "test_button_21",
                        "style": 2,
                        "label": "Secondary",
                    },
                    {
                        "type": 2,
                        "id": 22,
                        "custom_id": "test_button_22",
                        "style": 3,
                        "label": "Success",
                    },
                    {
                        "type": 2,
                        "id": 23,
                        "custom_id": "test_button_23",
                        "style": 4,
                        "label": "Danger",
                    },
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 2,
                        "id": 31,
                        "style": 5,
                        "label": "Link1",
                        "url": "https://docs.discord.com/developers/components/reference#button",
                    }
                ],
            },
        ]

    @pytest.fixture(scope="class")
    async def online_response(self, http_session, local_payload):
        flags = nextcord.MessageFlags()
        flags.is_components_v2 = True

        data = await http_session.send_message(
            utils.EnvVar.test_channel,
            None,
            components=local_payload,
            flags=flags.value,
        )
        return data["components"]

    @pytest.mark.skipif(utils.EnvVar.online is False, reason="Online only test.")
    async def test_online_against_offline_response(self, offline_response, online_response):
        assert offline_response == online_response

    def test_action_row_typings_against_offline_response(self, subtests, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.ActionRow)
        for orig_payload in offline_response:
            action_row_payload = orig_payload.copy()
            action_row_payload["components"] = []
            with subtests.test(
                msg="action row typing against payload without components",
                id=action_row_payload["id"],
            ):
                ta.validate_python(action_row_payload, extra="forbid")
            with subtests.test(
                msg="action row typing against payload with components", id=action_row_payload["id"]
            ):
                ta.validate_python(orig_payload, extra="forbid")

    def test_action_row_typings_against_comp_payload(self, subtests, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.ActionRow)
        for orig_payload in comp_payload:
            action_row_payload = orig_payload.copy()
            action_row_payload["components"] = []
            with subtests.test(
                msg="action row typing against payload without components",
                id=action_row_payload["id"],
            ):
                ta.validate_python(action_row_payload, extra="forbid")
            with subtests.test(
                msg="action row typing against payload with components", id=action_row_payload["id"]
            ):
                ta.validate_python(orig_payload, extra="forbid")

    def test_action_row_1_attributes(self, comps):
        action_row: nextcord.ActionRow = comps[0]
        assert action_row.type == 1
        assert action_row.id == 1
        assert len(action_row.components) == 5

    def test_action_row_1_offline_response(self, offline_response):
        data = offline_response[0].copy()
        data["components"] = []
        action_row: nextcord.ActionRow = nextcord.resolve_component(data)
        assert isinstance(action_row, nextcord.ActionRow)
        assert action_row.type == 1
        assert action_row.id == 1

    def test_action_row_2_attributes(self, comps):
        action_row: nextcord.ActionRow = comps[1]
        assert action_row.type == 1
        assert action_row.id == 2
        assert len(action_row.components) == 3

    def test_action_row_2_offline_response(self, offline_response):
        data = offline_response[1].copy()
        data["components"] = []
        action_row: nextcord.ActionRow = nextcord.resolve_component(data)
        assert isinstance(action_row, nextcord.ActionRow)
        assert action_row.type == 1
        assert action_row.id == 2

    def test_action_row_3_attributes(self, comps):
        action_row: nextcord.ActionRow = comps[2]
        assert action_row.type == 1
        assert action_row.id == 3
        assert len(action_row.components) == 1

    def test_action_row_3_offline_response(self, offline_response):
        data = offline_response[2].copy()
        data["components"] = []
        action_row: nextcord.ActionRow = nextcord.resolve_component(data)
        assert isinstance(action_row, nextcord.ActionRow)
        assert action_row.type == 1
        assert action_row.id == 3

    def test_button_primary_1_attributes(self, comps):
        button_1: nextcord.Button = comps[0].components[0]
        assert button_1.type == 2
        assert button_1.id == 11
        assert button_1.custom_id == "test_button_11"
        assert button_1.style == 1
        assert button_1.label == "Primary1"
        assert button_1.emoji is MISSING
        assert button_1.sku_id is MISSING
        assert button_1.url is MISSING
        assert button_1.disabled is MISSING

    def test_button_primary_1_offline_response(self, offline_response):
        button_1: nextcord.Button = nextcord.resolve_component(offline_response[0]["components"][0])
        assert isinstance(button_1, nextcord.Button)
        assert button_1.type == 2
        assert button_1.id == 11
        assert button_1.custom_id == "test_button_11"
        assert button_1.style == 1
        assert button_1.label == "Primary1"
        assert button_1.emoji is MISSING
        assert button_1.sku_id is MISSING
        assert button_1.url is MISSING
        assert button_1.disabled is MISSING

    def test_button_primary_2_attributes(self, comps):
        button_2: nextcord.Button = comps[0].components[1]
        assert button_2.type == 2
        assert button_2.id == 12
        assert button_2.custom_id == "test_button_12"
        assert button_2.style == 1
        assert button_2.label is MISSING
        assert button_2.emoji is not MISSING
        assert button_2.emoji.name == "⚠️"
        assert button_2.sku_id is MISSING
        assert button_2.url is MISSING
        assert button_2.disabled is MISSING

    def test_button_primary_2_offline_response(self, offline_response):
        button_2: nextcord.Button = nextcord.resolve_component(offline_response[0]["components"][1])
        assert isinstance(button_2, nextcord.Button)
        assert button_2.type == 2
        assert button_2.id == 12
        assert button_2.custom_id == "test_button_12"
        assert button_2.style == 1
        assert button_2.label is MISSING
        assert button_2.emoji is not MISSING
        assert button_2.emoji.name == "⚠️"
        assert button_2.sku_id is MISSING
        assert button_2.url is MISSING
        assert button_2.disabled is MISSING

    def test_button_primary_3_attributes(self, comps):
        button_3: nextcord.Button = comps[0].components[2]
        assert button_3.type == 2
        assert button_3.id == 13
        assert button_3.custom_id == "test_button_13"
        assert button_3.style == 1
        assert button_3.label == "Primary3"
        assert button_3.emoji is not MISSING
        assert button_3.emoji.name == "⚠️"
        assert button_3.sku_id is MISSING
        assert button_3.url is MISSING
        assert button_3.disabled is MISSING

    def test_button_primary_3_offline_response(self, offline_response):
        button_3: nextcord.Button = nextcord.resolve_component(offline_response[0]["components"][2])
        assert isinstance(button_3, nextcord.Button)
        assert button_3.type == 2
        assert button_3.id == 13
        assert button_3.custom_id == "test_button_13"
        assert button_3.style == 1
        assert button_3.label == "Primary3"
        assert button_3.emoji is not MISSING
        assert button_3.emoji.name == "⚠️"
        assert button_3.sku_id is MISSING
        assert button_3.url is MISSING
        assert button_3.disabled is MISSING

    def test_button_primary_4_attributes(self, comps):
        button_4: nextcord.Button = comps[0].components[3]
        assert button_4.type == 2
        assert button_4.id == 14
        assert button_4.style == 1
        assert button_4.custom_id == "test_button_14"
        assert button_4.label == "Primary4"
        assert button_4.emoji is MISSING
        assert button_4.sku_id is MISSING
        assert button_4.url is MISSING
        assert button_4.disabled is True

    def test_button_primary_4_offline_response(self, offline_response):
        button_4: nextcord.Button = nextcord.resolve_component(offline_response[0]["components"][3])
        assert isinstance(button_4, nextcord.Button)
        assert button_4.type == 2
        assert button_4.id == 14
        assert button_4.style == 1
        assert button_4.custom_id == "test_button_14"
        assert button_4.label == "Primary4"
        assert button_4.emoji is MISSING
        assert button_4.sku_id is MISSING
        assert button_4.url is MISSING
        assert button_4.disabled is True

    def test_button_primary_5_attributes(self, comps):
        button_5: nextcord.Button = comps[0].components[4]
        assert button_5.type == 2
        assert button_5.id == 15
        assert button_5.style == 1
        assert button_5.custom_id == "test_button_15"
        assert button_5.label == "Primary5"
        assert button_5.emoji is MISSING
        assert button_5.sku_id is MISSING
        assert button_5.url is MISSING
        assert button_5.disabled is False

    def test_button_primary_5_offline_response(self, offline_response):
        button_5: nextcord.Button = nextcord.resolve_component(offline_response[0]["components"][4])
        assert isinstance(button_5, nextcord.Button)
        assert button_5.type == 2
        assert button_5.id == 15
        assert button_5.style == 1
        assert button_5.custom_id == "test_button_15"
        assert button_5.label == "Primary5"
        assert button_5.emoji is MISSING
        assert button_5.sku_id is MISSING
        assert button_5.url is MISSING
        assert (
            button_5.disabled is MISSING
        )  # Discord currently doesn't return False, so this should be MISSING.

    def test_button_secondary_attributes(self, comps):
        button: nextcord.Button = comps[1].components[0]
        assert button.type == 2
        assert button.id == 21
        assert button.style == 2
        assert button.custom_id == "test_button_21"
        assert button.label == "Secondary"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    def test_button_secondary_offline_response(self, offline_response):
        button: nextcord.Button = nextcord.resolve_component(offline_response[1]["components"][0])
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 21
        assert button.style == 2
        assert button.custom_id == "test_button_21"
        assert button.label == "Secondary"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    def test_button_success_attributes(self, comps):
        button: nextcord.Button = comps[1].components[1]
        assert button.type == 2
        assert button.id == 22
        assert button.style == 3
        assert button.custom_id == "test_button_22"
        assert button.label == "Success"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    def test_button_success_offline_response(self, offline_response):
        button: nextcord.Button = nextcord.resolve_component(offline_response[1]["components"][1])
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 22
        assert button.style == 3
        assert button.custom_id == "test_button_22"
        assert button.label == "Success"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    def test_button_danger_attributes(self, comps):
        button: nextcord.Button = comps[1].components[2]
        assert button.type == 2
        assert button.id == 23
        assert button.style == 4
        assert button.custom_id == "test_button_23"
        assert button.label == "Danger"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    def test_button_danger_offline_response(self, offline_response):
        button: nextcord.Button = nextcord.resolve_component(offline_response[1]["components"][2])
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 23
        assert button.style == 4
        assert button.custom_id == "test_button_23"
        assert button.label == "Danger"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    def test_button_link_attributes(self, comps):
        button: nextcord.Button = comps[2].components[0]
        assert button.type == 2
        assert button.id == 31
        assert button.style == 5
        assert button.custom_id is MISSING
        assert button.label == "Link1"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url == "https://docs.discord.com/developers/components/reference#button"
        assert button.disabled is MISSING

    def test_button_link_offline_response(self, offline_response):
        button: nextcord.Button = nextcord.resolve_component(offline_response[2]["components"][0])
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 31
        assert button.style == 5
        assert button.custom_id is MISSING
        assert button.label == "Link1"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url == "https://docs.discord.com/developers/components/reference#button"
        assert button.disabled is MISSING

    # TODO: Add test for Premium button?
