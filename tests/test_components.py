# SPDX-License-Identifier: MIT

import pydantic
import pytest

import nextcord
from nextcord.types import components as comp_payloads
from nextcord.utils import MISSING
from tests import utils


def fixture_id(fixture_value):
    match fixture_value[0]:
        case "c":
            return f"comps {fixture_value[1]} {fixture_value[2]}"
        case "p":
            return f"comp_payload {fixture_value[1]} {fixture_value[2]}"
        case "o":
            return f"offline_response {fixture_value[1]} {fixture_value[2]}"
        case _:
            raise ValueError(f"Unhandled fixture value {fixture_value}")


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
    def saved_comp_payload(self):
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
                        "disabled": False,
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
    async def online_response(self, http_session, comp_payload):
        flags = nextcord.MessageFlags()
        flags.is_components_v2 = True

        data = await http_session.send_message(
            utils.EnvVar.test_channel,
            None,
            components=comp_payload,
            flags=flags.value,
        )
        return data["components"]

    @pytest.fixture(scope="class")
    def button(self, request: pytest.FixtureRequest, comps, comp_payload, offline_response):
        # Param should be a tuple of 3 values: (payload_source, action_row_index, button_index)
        match request.param[0]:
            case "c":
                return comps[request.param[1]].components[request.param[2]]
            case "p":
                return nextcord.resolve_component(
                    comp_payload[request.param[1]]["components"][request.param[2]]
                )
            case "o":
                return nextcord.resolve_component(
                    offline_response[request.param[1]]["components"][request.param[2]]
                )
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(utils.EnvVar.online is False, reason="Online only test.")
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "Offline response no longer matches online response, please update."

    def test_comp_payload_against_saved(self, comp_payload, saved_comp_payload):
        assert (
            comp_payload == saved_comp_payload
        ), "Saved button payload no longer matches generated payload, either update or fix."

    def test_comp_payload_typing(self, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.Component)
        for action_row in comp_payload:
            ta.validate_python(action_row, extra="forbid", strict=True)

    def test_offline_response_typing(self, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.Component)
        for action_row in offline_response:
            ta.validate_python(action_row, extra="forbid", strict=True)

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
                ta.validate_python(orig_payload, extra="forbid", strict=True)

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
                ta.validate_python(orig_payload, extra="forbid", strict=True)

    def test_button_typings_generated(self, subtests, comps):
        ta = pydantic.TypeAdapter(comp_payloads.ButtonComponent)
        for action_row in comps:
            assert isinstance(action_row, nextcord.ActionRow)
            for button in action_row.components:
                with subtests.test("Test comps payload typing", button=button):
                    ta.validate_python(button.to_dict(), extra="forbid", strict=True)

    def test_button_typings_offline_response(self, subtests, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.ButtonComponent)
        for action_row_data in offline_response:
            assert "components" in action_row_data
            for i, button_data in enumerate(action_row_data["components"]):
                with subtests.test("Test offline response typing", i=i, button_data=button_data):
                    ta.validate_python(button_data, extra="forbid", strict=True)

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

    @pytest.mark.parametrize(
        "button", [("c", 0, 0), ("p", 0, 0), ("o", 0, 0)], ids=fixture_id, indirect=True
    )
    def test_button_primary_1_attributes(self, button):
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 11
        assert button.custom_id == "test_button_11"
        assert button.style == 1
        assert button.label == "Primary1"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    @pytest.mark.parametrize(
        "button", [("c", 0, 1), ("p", 0, 1), ("o", 0, 1)], ids=fixture_id, indirect=True
    )
    def test_button_primary_2_attributes(self, button):
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 12
        assert button.custom_id == "test_button_12"
        assert button.style == 1
        assert button.label is MISSING
        assert button.emoji is not MISSING
        assert button.emoji.name == "⚠️"
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    @pytest.mark.parametrize(
        "button", [("c", 0, 2), ("p", 0, 2), ("o", 0, 2)], ids=fixture_id, indirect=True
    )
    def test_button_primary_3_attributes(self, button):
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 13
        assert button.custom_id == "test_button_13"
        assert button.style == 1
        assert button.label == "Primary3"
        assert button.emoji is not MISSING
        assert button.emoji.name == "⚠️"
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is MISSING

    @pytest.mark.parametrize(
        "button", [("c", 0, 3), ("p", 0, 3), ("o", 0, 3)], ids=fixture_id, indirect=True
    )
    def test_button_primary_4_attributes(self, button):
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 14
        assert button.style == 1
        assert button.custom_id == "test_button_14"
        assert button.label == "Primary4"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is True

    @pytest.mark.parametrize("button", [("c", 0, 4), ("p", 0, 4)], ids=fixture_id, indirect=True)
    def test_button_primary_5_attributes_generated(self, button):
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 15
        assert button.style == 1
        assert button.custom_id == "test_button_15"
        assert button.label == "Primary5"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert button.disabled is False

    @pytest.mark.parametrize("button", [("o", 0, 4)], ids=fixture_id, indirect=True)
    def test_button_primary_5_attributes_offline_response(self, button):
        """This separate test exists because Discord doesn't (currently) return button.disabled when it is explicitly
        set to False.
        """
        assert isinstance(button, nextcord.Button)
        assert button.type == 2
        assert button.id == 15
        assert button.style == 1
        assert button.custom_id == "test_button_15"
        assert button.label == "Primary5"
        assert button.emoji is MISSING
        assert button.sku_id is MISSING
        assert button.url is MISSING
        assert (
            button.disabled is MISSING
        )  # Discord currently doesn't return False, so this should be MISSING.

    @pytest.mark.parametrize(
        "button", [("c", 1, 0), ("p", 1, 0), ("o", 1, 0)], ids=fixture_id, indirect=True
    )
    def test_button_secondary_attributes(self, button):
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

    @pytest.mark.parametrize(
        "button", [("c", 1, 1), ("p", 1, 1), ("o", 1, 1)], ids=fixture_id, indirect=True
    )
    def test_button_success_attributes(self, button):
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

    @pytest.mark.parametrize(
        "button", [("c", 1, 2), ("p", 1, 2), ("o", 1, 2)], ids=fixture_id, indirect=True
    )
    def test_button_danger_attributes(self, button):
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

    @pytest.mark.parametrize(
        "button", [("c", 2, 0), ("p", 2, 0), ("o", 2, 0)], ids=fixture_id, indirect=True
    )
    def test_button_link_attributes(self, button):
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
