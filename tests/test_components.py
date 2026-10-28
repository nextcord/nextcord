# SPDX-License-Identifier: MIT

import pydantic
import pytest

import nextcord
from nextcord.types import components as comp_payloads
from nextcord.utils import MISSING
from tests import utils

__all__ = (
    "button_components",
    "string_select_components",
    "select_option_components",
)


async def send_components(http_session, comp_payload: list[dict]):
    assert utils.EnvVar.test_channel is not None
    flags = nextcord.MessageFlags()
    flags.is_components_v2 = True

    data = await http_session.send_message(
        utils.EnvVar.test_channel,
        None,
        components=comp_payload,
        flags=flags.value,
    )
    return data["components"]


def fixture_id(fixture_value):
    match fixture_value[0]:
        case "c":
            return f"comps {fixture_value[1:]}"
        case "p":
            return f"comp_payload {fixture_value[1:]}"
        case "o":
            return f"offline_response {fixture_value[1:]}"
        case _:
            raise ValueError(f"Unhandled fixture value {fixture_value}")


def test_base():
    assert True


def test_base_component_payload():
    ta = pydantic.TypeAdapter(comp_payloads.BaseComponent)
    ta.validate_python({"type": 1, "id": 1}, extra="forbid")


button_components = [
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
            nextcord.Button.as_danger(label="Danger", component_id=23, custom_id="test_button_23"),
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


class TestActionRowAndButtons:
    @pytest.fixture(scope="class")
    def comps(self) -> list[nextcord.Component]:
        return button_components

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
        return await send_components(http_session, comp_payload)

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

    @pytest.fixture(scope="class")
    def action_row(self, request: pytest.FixtureRequest, comps, comp_payload, offline_response):
        # Param should be a tuple of 2 values: (payload_source, action_row_index)
        match request.param[0]:
            case "c":
                return comps[request.param[1]]
            case "p":
                return nextcord.resolve_component(comp_payload[request.param[1]])
            case "o":
                return nextcord.resolve_component(offline_response[request.param[1]])
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(utils.EnvVar.online is False, reason="Online only test.")
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "Button offline response no longer matches online response, please update."

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

    @pytest.mark.parametrize(
        "action_row", [("c", 0), ("p", 0), ("o", 0)], ids=fixture_id, indirect=True
    )
    def test_action_row_1_attributes(self, action_row):
        assert isinstance(action_row, nextcord.ActionRow)
        assert action_row.type == 1
        assert action_row.id == 1
        assert len(action_row.components) == 5

    @pytest.mark.parametrize(
        "action_row", [("c", 1), ("p", 1), ("o", 1)], ids=fixture_id, indirect=True
    )
    def test_action_row_2_attributes(self, action_row):
        assert isinstance(action_row, nextcord.ActionRow)
        assert action_row.type == 1
        assert action_row.id == 2
        assert len(action_row.components) == 3

    @pytest.mark.parametrize(
        "action_row", [("c", 2), ("p", 2), ("o", 2)], ids=fixture_id, indirect=True
    )
    def test_action_row_3_attributes(self, action_row):
        assert isinstance(action_row, nextcord.ActionRow)
        assert action_row.type == 1
        assert action_row.id == 3
        assert len(action_row.components) == 1

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


select_option_components = [
    nextcord.SelectOption(label="Zeroth"),
    nextcord.SelectOption(label="First", default=True),
    nextcord.SelectOption(label="Second", value="2nd"),
    nextcord.SelectOption(label="Third", description="The third one."),
    nextcord.SelectOption(label="Fourth", default=False),
    nextcord.SelectOption(label="Fifth", emoji="⚠️"),
    nextcord.SelectOption(label="Sixth", emoji=nextcord.PartialEmoji(name="⚠️")),
]


class TestSelectOption:
    @pytest.fixture(scope="class")
    def comps(self):
        return select_option_components

    @pytest.fixture(scope="class")
    def comp_payload(self, comps):
        return [comp.to_dict() for comp in comps]

    @pytest.fixture(scope="class")
    def saved_comp_payload(self):
        return [
            {"label": "Zeroth", "value": "Zeroth"},
            {"label": "First", "value": "First", "default": True},
            {"label": "Second", "value": "2nd"},
            {"label": "Third", "value": "Third", "description": "The third one."},
            {"label": "Fourth", "value": "Fourth", "default": False},
            {"label": "Fifth", "value": "Fifth", "emoji": {"name": "⚠️"}},
            {"label": "Sixth", "value": "Sixth", "emoji": {"name": "⚠️"}},
        ]

    @pytest.fixture(scope="class")
    def offline_response(self):
        return [
            {"label": "Zeroth", "value": "Zeroth"},
            {"label": "First", "value": "First", "default": True},
            {"label": "Second", "value": "2nd"},
            {"label": "Third", "value": "Third", "description": "The third one."},
            {"label": "Fourth", "value": "Fourth"},
            {"label": "Fifth", "value": "Fifth", "emoji": {"name": "⚠️"}},
            {"label": "Sixth", "value": "Sixth", "emoji": {"name": "⚠️"}},
        ]

    @pytest.fixture(scope="class")
    async def online_response(self, http_session, comps):
        wrapped_comps = [nextcord.ActionRow([nextcord.StringSelect(options=comps)])]
        data = await send_components(http_session, [comp.to_dict() for comp in wrapped_comps])
        return data[0]["components"][0]["options"]

    @pytest.fixture(scope="class")
    def option(self, request: pytest.FixtureRequest, comps, comp_payload, offline_response):
        match request.param[0]:
            case "c":
                return comps[request.param[1]]
            case "p":
                return nextcord.SelectOption.from_dict(comp_payload[request.param[1]])
            case "o":
                return nextcord.SelectOption.from_dict(offline_response[request.param[1]])
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(
        utils.EnvVar.online is False or utils.EnvVar.test_channel is None,
        reason="Online only test, requires TEST_CHANNEL to be set.",
    )
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "SelectOption offline response no longer matches online response, please update."

    def test_comp_payload_against_saved(self, comp_payload, saved_comp_payload):
        assert (
            comp_payload == saved_comp_payload
        ), "Saved SelectOption payload no longer matches generated payload, either update or fix."

    def test_comp_payload_typing(self, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.SelectOption)
        for data in comp_payload:
            ta.validate_python(data, extra="forbid", strict=True)

    def test_offline_response_typing(self, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.SelectOption)
        for data in offline_response:
            ta.validate_python(data, extra="forbid", strict=True)

    @pytest.mark.parametrize(
        "option", [("c", 0), ("p", 0), ("o", 0)], ids=fixture_id, indirect=True
    )
    def test_zeroth_attributes(self, option):
        assert option.label == "Zeroth"
        assert option.value == "Zeroth"
        assert option.description is MISSING
        assert option.emoji is MISSING
        assert option.default is MISSING

    @pytest.mark.parametrize(
        "option", [("c", 1), ("p", 1), ("o", 1)], ids=fixture_id, indirect=True
    )
    def test_first_attributes(self, option):
        assert option.label == "First"
        assert option.value == "First"
        assert option.description is MISSING
        assert option.emoji is MISSING
        assert option.default is True

    @pytest.mark.parametrize(
        "option", [("c", 2), ("p", 2), ("o", 2)], ids=fixture_id, indirect=True
    )
    def test_second_attributes(self, option):
        assert option.label == "Second"
        assert option.value == "2nd"
        assert option.description is MISSING
        assert option.emoji is MISSING
        assert option.default is MISSING

    @pytest.mark.parametrize(
        "option", [("c", 3), ("p", 3), ("o", 3)], ids=fixture_id, indirect=True
    )
    def test_third_attributes(self, option):
        assert option.label == "Third"
        assert option.value == "Third"
        assert option.description == "The third one."
        assert option.emoji is MISSING
        assert option.default is MISSING

    @pytest.mark.parametrize("option", [("c", 4), ("p", 4)], ids=fixture_id, indirect=True)
    def test_fourth_attributes_comp(self, option):
        assert option.label == "Fourth"
        assert option.value == "Fourth"
        assert option.description is MISSING
        assert option.emoji is MISSING
        assert option.default is False

    @pytest.mark.parametrize("option", [("o", 4)], ids=fixture_id, indirect=True)
    def test_forth_attributes_offline_response(self, option):
        assert option.label == "Fourth"
        assert option.value == "Fourth"
        assert option.description is MISSING
        assert option.emoji is MISSING
        assert option.default is MISSING  # Discord doesn't return default if it is set to False.

    @pytest.mark.parametrize(
        "option", [("c", 5), ("p", 5), ("o", 5)], ids=fixture_id, indirect=True
    )
    def test_fifth_attributes(self, option):
        assert option.label == "Fifth"
        assert option.value == "Fifth"
        assert option.description is MISSING
        assert option.emoji is not MISSING
        assert option.emoji.name == "⚠️"
        assert option.default is MISSING

    @pytest.mark.parametrize(
        "option", [("c", 6), ("p", 6), ("o", 6)], ids=fixture_id, indirect=True
    )
    def test_sixth_attributes(self, option):
        assert option.label == "Sixth"
        assert option.value == "Sixth"
        assert option.description is MISSING
        assert option.emoji is not MISSING
        assert option.emoji.name == "⚠️"
        assert option.default is MISSING


_string_select_options = [
    nextcord.SelectOption(label="First"),
    nextcord.SelectOption(label="Second", value="2nd"),
    nextcord.SelectOption(label="Third", description="The third one."),
]
string_select_components = [
    nextcord.ActionRow(
        [
            nextcord.StringSelect(
                options=_string_select_options, custom_id="test_string_select_1", component_id=10
            )
        ],
        component_id=1,
    ),
    nextcord.ActionRow(
        [
            nextcord.StringSelect(
                options=_string_select_options,
                placeholder="Placeholder text",
                custom_id="test_string_select_2",
                component_id=20,
            )
        ],
        component_id=2,
    ),
    nextcord.ActionRow(
        [
            nextcord.StringSelect(
                options=_string_select_options,
                min_values=1,
                custom_id="test_string_select_3",
                component_id=30,
            )
        ],
        component_id=3,
    ),
    nextcord.ActionRow(
        [
            nextcord.StringSelect(
                options=_string_select_options,
                max_values=2,
                custom_id="test_string_select_4",
                component_id=40,
            )
        ],
        component_id=4,
    ),
    nextcord.ActionRow(
        [
            nextcord.StringSelect(
                options=_string_select_options,
                min_values=2,
                max_values=3,
                custom_id="test_string_select_5",
                component_id=50,
            )
        ],
        component_id=5,
    ),
    nextcord.ActionRow(
        [
            nextcord.StringSelect(
                options=_string_select_options,
                disabled=True,
                custom_id="test_string_select_6",
                component_id=60,
            )
        ],
        component_id=6,
    ),
]


class TestStringSelects:
    @pytest.fixture(scope="class")
    def comps(self):
        return string_select_components

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
                        "type": 3,
                        "id": 10,
                        "custom_id": "test_string_select_1",
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 3,
                        "id": 20,
                        "custom_id": "test_string_select_2",
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                        "placeholder": "Placeholder text",
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 3,
                        "id": 30,
                        "custom_id": "test_string_select_3",
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                        "min_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 3,
                        "id": 40,
                        "custom_id": "test_string_select_4",
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                        "max_values": 2,
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 3,
                        "id": 50,
                        "custom_id": "test_string_select_5",
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 6,
                "components": [
                    {
                        "type": 3,
                        "id": 60,
                        "custom_id": "test_string_select_6",
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                        "disabled": True,
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
                        "type": 3,
                        "id": 10,
                        "custom_id": "test_string_select_1",
                        "min_values": 1,
                        "max_values": 1,
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 3,
                        "id": 20,
                        "custom_id": "test_string_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 3,
                        "id": 30,
                        "custom_id": "test_string_select_3",
                        "min_values": 1,
                        "max_values": 1,
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 3,
                        "id": 40,
                        "custom_id": "test_string_select_4",
                        "min_values": 1,
                        "max_values": 2,
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 3,
                        "id": 50,
                        "custom_id": "test_string_select_5",
                        "min_values": 2,
                        "max_values": 3,
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 6,
                "components": [
                    {
                        "type": 3,
                        "id": 60,
                        "custom_id": "test_string_select_6",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
                        "options": [
                            {"label": "First", "value": "First"},
                            {"label": "Second", "value": "2nd"},
                            {"label": "Third", "value": "Third", "description": "The third one."},
                        ],
                    }
                ],
            },
        ]

    @pytest.fixture(scope="class")
    async def online_response(self, http_session, comp_payload):
        return await send_components(http_session, comp_payload)

    @pytest.fixture(scope="class")
    def string_select(self, request: pytest.FixtureRequest, comps, comp_payload, offline_response):
        # Param should be a tuple of 2 values: (payload_source, action_row_index)
        match request.param[0]:
            case "c":
                return comps[request.param[1]].components[0]
            case "p":
                return nextcord.resolve_component(comp_payload[request.param[1]]["components"][0])
            case "o":
                return nextcord.resolve_component(
                    offline_response[request.param[1]]["components"][0]
                )
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(
        utils.EnvVar.online is False or utils.EnvVar.test_channel is None,
        reason="Online only test, requires TEST_CHANNEL to be set.",
    )
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "StringSelect offline response no longer matches online response, please update."

    def test_comp_payload_against_saved(self, comp_payload, saved_comp_payload):
        assert (
            comp_payload == saved_comp_payload
        ), "Saved StringSelect payload no longer matches generated payload, either update or fix."

    def test_comp_payload_typing(self, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.SelectMenu)
        for data in comp_payload:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_offline_response_typing(self, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.SelectMenu)
        for data in offline_response:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_select_menu_alias(self):
        assert nextcord.SelectMenu is nextcord.StringSelect

    def test_string_select_menu_alias(self):
        assert nextcord.StringSelectMenu is nextcord.StringSelect

    def _assert_options(self, select: nextcord.StringSelect):
        assert select.options[0].label == "First"
        assert select.options[1].label == "Second"
        assert select.options[1].value == "2nd"
        assert select.options[2].label == "Third"
        assert select.options[2].description == "The third one."
        return True

    @pytest.mark.parametrize("string_select", [("c", 0), ("p", 0)], ids=fixture_id, indirect=True)
    def test_string_select_1_payload_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 10
        assert string_select.custom_id == "test_string_select_1"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values is MISSING
        assert string_select.max_values is MISSING
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("o", 0)], ids=fixture_id, indirect=True)
    def test_string_select_1_offline_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 10
        assert string_select.custom_id == "test_string_select_1"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert (
            string_select.min_values == 1
        )  # Discord returns 1 for min and max values, even if we don't include them in the payload.
        assert string_select.max_values == 1
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("c", 1), ("p", 1)], ids=fixture_id, indirect=True)
    def test_string_select_2_payload_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 20
        assert string_select.custom_id == "test_string_select_2"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder == "Placeholder text"
        assert string_select.min_values is MISSING
        assert string_select.max_values is MISSING
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("o", 1)], ids=fixture_id, indirect=True)
    def test_string_select_2_offline_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 20
        assert string_select.custom_id == "test_string_select_2"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder == "Placeholder text"
        assert string_select.min_values == 1
        assert string_select.max_values == 1
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("c", 2), ("p", 2)], ids=fixture_id, indirect=True)
    def test_string_select_3_payload_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 30
        assert string_select.custom_id == "test_string_select_3"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values == 1
        assert string_select.max_values is MISSING
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("o", 2)], ids=fixture_id, indirect=True)
    def test_string_select_3_offline_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 30
        assert string_select.custom_id == "test_string_select_3"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values == 1
        assert string_select.max_values == 1
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("c", 3), ("p", 3)], ids=fixture_id, indirect=True)
    def test_string_select_4_payload_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 40
        assert string_select.custom_id == "test_string_select_4"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values is MISSING
        assert string_select.max_values == 2
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("o", 3)], ids=fixture_id, indirect=True)
    def test_string_select_4_offline_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 40
        assert string_select.custom_id == "test_string_select_4"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values == 1
        assert string_select.max_values == 2
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize(
        "string_select", [("c", 4), ("p", 4), ("o", 4)], ids=fixture_id, indirect=True
    )
    def test_string_select_5_payload_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 50
        assert string_select.custom_id == "test_string_select_5"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values == 2
        assert string_select.max_values == 3
        assert string_select.disabled is MISSING

    @pytest.mark.parametrize("string_select", [("c", 5), ("p", 5)], ids=fixture_id, indirect=True)
    def test_string_select_6_payload_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 60
        assert string_select.custom_id == "test_string_select_6"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values is MISSING
        assert string_select.max_values is MISSING
        assert string_select.disabled is True

    @pytest.mark.parametrize("string_select", [("o", 5)], ids=fixture_id, indirect=True)
    def test_string_select_6_offline_attributes(self, string_select):
        assert isinstance(string_select, nextcord.StringSelect)
        assert string_select.id == 60
        assert string_select.custom_id == "test_string_select_6"
        assert len(string_select.options) == 3
        self._assert_options(string_select)
        assert string_select.placeholder is MISSING
        assert string_select.min_values == 1
        assert string_select.max_values == 1
        assert string_select.disabled is True


user_select_components = [
    nextcord.ActionRow(
        [nextcord.UserSelect(custom_id="test_user_select_1", component_id=10)], component_id=1
    ),
    nextcord.ActionRow(
        [
            nextcord.UserSelect(
                placeholder="Placeholder text",
                min_values=1,
                max_values=1,
                custom_id="test_user_select_2",
                component_id=20,
            ),
        ],
        component_id=2,
    ),
    nextcord.ActionRow(
        [
            nextcord.UserSelect(
                min_values=2, max_values=3, custom_id="test_user_select_3", component_id=30
            )
        ],
        component_id=3,
    ),
    nextcord.ActionRow(
        [
            nextcord.UserSelect(
                default_values=[
                    nextcord.SelectDefaultValue(
                        utils.EnvVar.test_user, nextcord.SelectDefaultValueType.user
                    )
                ],
                min_values=1,
                max_values=1,
                custom_id="test_user_select_4",
                component_id=40,
            )
        ],
        component_id=4,
    ),
    nextcord.ActionRow(
        [
            nextcord.UserSelect(
                disabled=True,
                min_values=1,
                max_values=1,
                custom_id="test_user_select_5",
                component_id=50,
            )
        ],
        component_id=5,
    ),
]


@pytest.mark.skipif(utils.EnvVar.test_user is None, reason="Requires TEST_USER envvar to be set.")
class TestUserSelects:
    @pytest.fixture(scope="class")
    def comps(self):
        return user_select_components

    @pytest.fixture(scope="class")
    def comp_payload(self, comps):
        return [comp.to_dict() for comp in comps]

    @pytest.fixture(scope="class")
    def saved_comp_payload(self):
        return [
            {
                "type": 1,
                "id": 1,
                "components": [{"type": 5, "id": 10, "custom_id": "test_user_select_1"}],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 5,
                        "id": 20,
                        "custom_id": "test_user_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 5,
                        "id": 30,
                        "custom_id": "test_user_select_3",
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 5,
                        "id": 40,
                        "custom_id": "test_user_select_4",
                        "default_values": [{"id": utils.EnvVar.test_user, "type": "user"}],
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 5,
                        "id": 50,
                        "custom_id": "test_user_select_5",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
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
                        "type": 5,
                        "id": 10,
                        "custom_id": "test_user_select_1",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 5,
                        "id": 20,
                        "custom_id": "test_user_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 5,
                        "id": 30,
                        "custom_id": "test_user_select_3",
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 5,
                        "id": 40,
                        "custom_id": "test_user_select_4",
                        "min_values": 1,
                        "max_values": 1,
                        "default_values": [{"type": "user", "id": f"{utils.EnvVar.test_user}"}],
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 5,
                        "id": 50,
                        "custom_id": "test_user_select_5",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
                    }
                ],
            },
        ]

    @pytest.fixture(scope="class")
    async def online_response(self, http_session, comp_payload):
        return await send_components(http_session, comp_payload)

    @pytest.fixture(scope="class")
    def user_select(self, request: pytest.FixtureRequest, comps, comp_payload, offline_response):
        # Param should be a tuple of 2 values: (payload_source, action_row_index)
        match request.param[0]:
            case "c":
                return comps[request.param[1]].components[0]
            case "p":
                return nextcord.resolve_component(comp_payload[request.param[1]]["components"][0])
            case "o":
                return nextcord.resolve_component(
                    offline_response[request.param[1]]["components"][0]
                )
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(
        utils.EnvVar.online is False or utils.EnvVar.test_channel is None,
        reason="Online only test, requires TEST_CHANNEL to be set.",
    )
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "UserSelect offline response no longer matches online response, please update."

    def test_comp_payload_against_saved(self, comp_payload, saved_comp_payload):
        assert (
            comp_payload == saved_comp_payload
        ), "Saved UserSelect payload no longer matches generated payload, either update or fix."

    def test_comp_payload_typing(self, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.UserSelectMenu)
        for data in comp_payload:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_offline_response_typing(self, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.UserSelectMenu)
        for data in offline_response:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_select_menu_alias(self):
        assert nextcord.UserSelectMenu is nextcord.UserSelect

    @pytest.mark.parametrize("user_select", [("c", 0), ("p", 0)], ids=fixture_id, indirect=True)
    def test_user_select_1_payload_attributes(self, user_select):
        assert isinstance(user_select, nextcord.UserSelect)
        assert user_select.id == 10
        assert user_select.custom_id == "test_user_select_1"
        assert user_select.placeholder is MISSING
        assert user_select.default_values is MISSING
        assert user_select.min_values is MISSING
        assert user_select.max_values is MISSING
        assert user_select.disabled is MISSING

    @pytest.mark.parametrize("user_select", [("o", 0)], ids=fixture_id, indirect=True)
    def test_user_select_1_offline_attributes(self, user_select):
        assert isinstance(user_select, nextcord.UserSelect)
        assert user_select.id == 10
        assert user_select.custom_id == "test_user_select_1"
        assert user_select.placeholder is MISSING
        assert user_select.default_values is MISSING
        assert user_select.min_values == 1
        assert user_select.max_values == 1
        assert user_select.disabled is MISSING

    @pytest.mark.parametrize(
        "user_select", [("c", 1), ("p", 1), ("o", 1)], ids=fixture_id, indirect=True
    )
    def test_user_select_2_attributes(self, user_select):
        assert isinstance(user_select, nextcord.UserSelect)
        assert user_select.id == 20
        assert user_select.custom_id == "test_user_select_2"
        assert user_select.placeholder == "Placeholder text"
        assert user_select.default_values is MISSING
        assert user_select.min_values == 1
        assert user_select.max_values == 1
        assert user_select.disabled is MISSING

    @pytest.mark.parametrize(
        "user_select", [("c", 2), ("p", 2), ("o", 2)], ids=fixture_id, indirect=True
    )
    def test_user_select_3_attributes(self, user_select):
        assert isinstance(user_select, nextcord.UserSelect)
        assert user_select.id == 30
        assert user_select.custom_id == "test_user_select_3"
        assert user_select.placeholder is MISSING
        assert user_select.default_values is MISSING
        assert user_select.min_values == 2
        assert user_select.max_values == 3
        assert user_select.disabled is MISSING

    @pytest.mark.parametrize(
        "user_select", [("c", 3), ("p", 3), ("o", 3)], ids=fixture_id, indirect=True
    )
    def test_user_select_4_attributes(self, user_select):
        assert isinstance(user_select, nextcord.UserSelect)
        assert user_select.id == 40
        assert user_select.custom_id == "test_user_select_4"
        assert user_select.placeholder is MISSING
        assert user_select.default_values is not MISSING
        assert len(user_select.default_values) == 1
        assert user_select.default_values[0].id == utils.EnvVar.test_user
        assert user_select.default_values[0].type == nextcord.SelectDefaultValueType.user
        assert user_select.min_values == 1
        assert user_select.max_values == 1
        assert user_select.disabled is MISSING

    @pytest.mark.parametrize(
        "user_select", [("c", 4), ("p", 4), ("o", 4)], ids=fixture_id, indirect=True
    )
    def test_user_select_5_attributes(self, user_select):
        assert isinstance(user_select, nextcord.UserSelect)
        assert user_select.id == 50
        assert user_select.custom_id == "test_user_select_5"
        assert user_select.placeholder is MISSING
        assert user_select.default_values is MISSING
        assert user_select.min_values == 1
        assert user_select.max_values == 1
        assert user_select.disabled is True

    def test_user_select_add_default(self):
        select = nextcord.UserSelect()
        assert select.default_values is MISSING
        select.add_default_value(111111)
        assert select.default_values is not MISSING
        assert len(select.default_values) == 1
        assert select.default_values[0].id == 111111
        assert select.default_values[0].type == nextcord.SelectDefaultValueType.user


role_select_components = [
    nextcord.ActionRow(
        [nextcord.RoleSelect(custom_id="test_role_select_1", component_id=10)], component_id=1
    ),
    nextcord.ActionRow(
        [
            nextcord.RoleSelect(
                placeholder="Placeholder text",
                min_values=1,
                max_values=1,
                custom_id="test_role_select_2",
                component_id=20,
            )
        ],
        component_id=2,
    ),
    nextcord.ActionRow(
        [
            nextcord.RoleSelect(
                min_values=2, max_values=3, custom_id="test_role_select_3", component_id=30
            )
        ],
        component_id=3,
    ),
    nextcord.ActionRow(
        [
            nextcord.RoleSelect(
                default_values=[
                    nextcord.SelectDefaultValue(
                        utils.EnvVar.test_role, nextcord.SelectDefaultValueType.role
                    )
                ],
                min_values=1,
                max_values=1,
                custom_id="test_role_select_4",
                component_id=40,
            )
        ],
        component_id=4,
    ),
    nextcord.ActionRow(
        [
            nextcord.RoleSelect(
                disabled=True,
                min_values=1,
                max_values=1,
                custom_id="test_role_select_5",
                component_id=50,
            )
        ],
        component_id=5,
    ),
]


@pytest.mark.skipif(utils.EnvVar.test_role is None, reason="Requires TEST_ROLE envvar to be set.")
class TestRoleSelects:
    @pytest.fixture(scope="class")
    def comps(self):
        return role_select_components

    @pytest.fixture(scope="class")
    def comp_payload(self, comps):
        return [comp.to_dict() for comp in comps]

    @pytest.fixture(scope="class")
    def saved_comp_payload(self):
        return [
            {
                "type": 1,
                "id": 1,
                "components": [{"type": 6, "id": 10, "custom_id": "test_role_select_1"}],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 6,
                        "id": 20,
                        "custom_id": "test_role_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 6,
                        "id": 30,
                        "custom_id": "test_role_select_3",
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 6,
                        "id": 40,
                        "custom_id": "test_role_select_4",
                        "default_values": [{"id": utils.EnvVar.test_role, "type": "role"}],
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 6,
                        "id": 50,
                        "custom_id": "test_role_select_5",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
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
                        "type": 6,
                        "id": 10,
                        "custom_id": "test_role_select_1",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 6,
                        "id": 20,
                        "custom_id": "test_role_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 6,
                        "id": 30,
                        "custom_id": "test_role_select_3",
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 6,
                        "id": 40,
                        "custom_id": "test_role_select_4",
                        "min_values": 1,
                        "max_values": 1,
                        "default_values": [{"type": "role", "id": f"{utils.EnvVar.test_role}"}],
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 6,
                        "id": 50,
                        "custom_id": "test_role_select_5",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
                    }
                ],
            },
        ]

    @pytest.fixture(scope="class")
    async def online_response(self, http_session, comp_payload):
        return await send_components(http_session, comp_payload)

    @pytest.fixture(scope="class")
    def role_select(self, request: pytest.FixtureRequest, comps, comp_payload, offline_response):
        # Param should be a tuple of 2 values: (payload_source, action_row_index)
        match request.param[0]:
            case "c":
                return comps[request.param[1]].components[0]
            case "p":
                return nextcord.resolve_component(comp_payload[request.param[1]]["components"][0])
            case "o":
                return nextcord.resolve_component(
                    offline_response[request.param[1]]["components"][0]
                )
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(
        utils.EnvVar.online is False or utils.EnvVar.test_channel is None,
        reason="Online only test, requires TEST_CHANNEL to be set.",
    )
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "RoleSelect offline response no longer matches online response, please update."

    def test_comp_payload_against_saved(self, comp_payload, saved_comp_payload):
        assert (
            comp_payload == saved_comp_payload
        ), "Saved RoleSelect payload no longer matches generate, either update or fix."

    def test_comp_payload_typing(self, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.RoleSelectMenu)
        for data in comp_payload:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_offline_response_typing(self, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.RoleSelectMenu)
        for data in offline_response:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_select_menu_alias(self):
        assert nextcord.RoleSelectMenu is nextcord.RoleSelect

    @pytest.mark.parametrize("role_select", [("c", 0), ("p", 0)], ids=fixture_id, indirect=True)
    def test_role_select_1_payload_attributes(self, role_select):
        assert isinstance(role_select, nextcord.RoleSelect)
        assert role_select.id == 10
        assert role_select.custom_id == "test_role_select_1"
        assert role_select.placeholder is MISSING
        assert role_select.default_values is MISSING
        assert role_select.min_values is MISSING
        assert role_select.max_values is MISSING
        assert role_select.disabled is MISSING

    @pytest.mark.parametrize("role_select", [("o", 0)], ids=fixture_id, indirect=True)
    def test_role_select_1_offline_attributes(self, role_select):
        assert isinstance(role_select, nextcord.RoleSelect)
        assert role_select.id == 10
        assert role_select.custom_id == "test_role_select_1"
        assert role_select.placeholder is MISSING
        assert role_select.default_values is MISSING
        assert role_select.min_values == 1
        assert role_select.max_values == 1
        assert role_select.disabled is MISSING

    @pytest.mark.parametrize(
        "role_select", [("c", 1), ("p", 1), ("o", 1)], ids=fixture_id, indirect=True
    )
    def test_role_select_2_attributes(self, role_select):
        assert isinstance(role_select, nextcord.RoleSelect)
        assert role_select.id == 20
        assert role_select.custom_id == "test_role_select_2"
        assert role_select.placeholder == "Placeholder text"
        assert role_select.default_values is MISSING
        assert role_select.min_values == 1
        assert role_select.max_values == 1
        assert role_select.disabled is MISSING

    @pytest.mark.parametrize(
        "role_select", [("c", 2), ("p", 2), ("o", 2)], ids=fixture_id, indirect=True
    )
    def test_role_select_3_attributes(self, role_select):
        assert isinstance(role_select, nextcord.RoleSelect)
        assert role_select.id == 30
        assert role_select.custom_id == "test_role_select_3"
        assert role_select.placeholder is MISSING
        assert role_select.default_values is MISSING
        assert role_select.min_values == 2
        assert role_select.max_values == 3
        assert role_select.disabled is MISSING

    @pytest.mark.parametrize(
        "role_select", [("c", 3), ("p", 3), ("o", 3)], ids=fixture_id, indirect=True
    )
    def test_role_select_4_attributes(self, role_select):
        assert isinstance(role_select, nextcord.RoleSelect)
        assert role_select.id == 40
        assert role_select.custom_id == "test_role_select_4"
        assert role_select.placeholder is MISSING
        assert role_select.default_values is not MISSING
        assert len(role_select.default_values) == 1
        assert role_select.default_values[0].id == utils.EnvVar.test_role
        assert role_select.default_values[0].type == nextcord.SelectDefaultValueType.role
        assert role_select.min_values == 1
        assert role_select.max_values == 1
        assert role_select.disabled is MISSING

    @pytest.mark.parametrize(
        "role_select", [("c", 4), ("p", 4), ("o", 4)], ids=fixture_id, indirect=True
    )
    def test_role_select_5_attributes(self, role_select):
        assert isinstance(role_select, nextcord.RoleSelect)
        assert role_select.id == 50
        assert role_select.custom_id == "test_role_select_5"
        assert role_select.placeholder is MISSING
        assert role_select.default_values is MISSING
        assert role_select.min_values == 1
        assert role_select.max_values == 1
        assert role_select.disabled is True

    def test_role_select_add_default(self):
        select = nextcord.RoleSelect()
        assert select.default_values is MISSING
        select.add_default_value(utils.EnvVar.test_role)
        assert select.default_values is not MISSING
        assert len(select.default_values) == 1
        assert select.default_values[0].id == utils.EnvVar.test_role
        assert select.default_values[0].type == nextcord.SelectDefaultValueType.role


mentionable_select_components = [
    nextcord.ActionRow(
        [nextcord.MentionableSelect(custom_id="test_mentionable_select_1", component_id=10)],
        component_id=1,
    ),
    nextcord.ActionRow(
        [
            nextcord.MentionableSelect(
                placeholder="Placeholder text",
                min_values=1,
                max_values=1,
                custom_id="test_mentionable_select_2",
                component_id=20,
            )
        ],
        component_id=2,
    ),
    nextcord.ActionRow(
        [
            nextcord.MentionableSelect(
                min_values=2, max_values=3, custom_id="test_mentionable_select_3", component_id=30
            )
        ],
        component_id=3,
    ),
    nextcord.ActionRow(
        [
            nextcord.MentionableSelect(
                default_values=[
                    nextcord.SelectDefaultValue(
                        utils.EnvVar.test_user, nextcord.SelectDefaultValueType.user
                    ),
                    nextcord.SelectDefaultValue(
                        utils.EnvVar.test_role, nextcord.SelectDefaultValueType.role
                    ),
                ],
                min_values=1,
                max_values=2,
                custom_id="test_mentionable_select_4",
                component_id=40,
            )
        ],
        component_id=4,
    ),
    nextcord.ActionRow(
        [
            nextcord.MentionableSelect(
                disabled=True,
                min_values=1,
                max_values=1,
                custom_id="test_mentionable_select_5",
                component_id=50,
            )
        ],
        component_id=5,
    ),
]


@pytest.mark.skipif(
    utils.EnvVar.test_user is None or utils.EnvVar.test_role is None,
    reason="Requires TEST_USER and TEST_ROLE envvars to be set.",
)
class TestMentionableSelects:
    @pytest.fixture(scope="class")
    def comps(self):
        return mentionable_select_components

    @pytest.fixture(scope="class")
    def comp_payload(self, comps):
        return [comp.to_dict() for comp in comps]

    @pytest.fixture(scope="class")
    def saved_comp_payload(self):
        return [
            {
                "type": 1,
                "id": 1,
                "components": [{"type": 7, "id": 10, "custom_id": "test_mentionable_select_1"}],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 7,
                        "id": 20,
                        "custom_id": "test_mentionable_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 7,
                        "id": 30,
                        "custom_id": "test_mentionable_select_3",
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 7,
                        "id": 40,
                        "custom_id": "test_mentionable_select_4",
                        "default_values": [
                            {"id": utils.EnvVar.test_user, "type": "user"},
                            {"id": utils.EnvVar.test_role, "type": "role"},
                        ],
                        "min_values": 1,
                        "max_values": 2,
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 7,
                        "id": 50,
                        "custom_id": "test_mentionable_select_5",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
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
                        "type": 7,
                        "id": 10,
                        "custom_id": "test_mentionable_select_1",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 2,
                "components": [
                    {
                        "type": 7,
                        "id": 20,
                        "custom_id": "test_mentionable_select_2",
                        "placeholder": "Placeholder text",
                        "min_values": 1,
                        "max_values": 1,
                    }
                ],
            },
            {
                "type": 1,
                "id": 3,
                "components": [
                    {
                        "type": 7,
                        "id": 30,
                        "custom_id": "test_mentionable_select_3",
                        "min_values": 2,
                        "max_values": 3,
                    }
                ],
            },
            {
                "type": 1,
                "id": 4,
                "components": [
                    {
                        "type": 7,
                        "id": 40,
                        "custom_id": "test_mentionable_select_4",
                        "min_values": 1,
                        "max_values": 2,
                        "default_values": [
                            {"type": "user", "id": f"{utils.EnvVar.test_user}"},
                            {"type": "role", "id": f"{utils.EnvVar.test_role}"},
                        ],
                    }
                ],
            },
            {
                "type": 1,
                "id": 5,
                "components": [
                    {
                        "type": 7,
                        "id": 50,
                        "custom_id": "test_mentionable_select_5",
                        "min_values": 1,
                        "max_values": 1,
                        "disabled": True,
                    }
                ],
            },
        ]

    @pytest.fixture(scope="class")
    async def online_response(self, http_session, comp_payload):
        return await send_components(http_session, comp_payload)

    @pytest.fixture(scope="class")
    def mentionable_select(
        self, request: pytest.FixtureRequest, comps, comp_payload, offline_response
    ):
        # Param should be a tuple of 2 values: (payload_source, action_row_index)
        match request.param[0]:
            case "c":
                return comps[request.param[1]].components[0]
            case "p":
                return nextcord.resolve_component(comp_payload[request.param[1]]["components"][0])
            case "o":
                return nextcord.resolve_component(
                    offline_response[request.param[1]]["components"][0]
                )
            case _:
                raise ValueError(f"Unhandled request param value {request.param}")

    @pytest.mark.skipif(
        utils.EnvVar.online is False or utils.EnvVar.test_channel is None,
        reason="Online only test, requires TEST_CHANNEL to be set.",
    )
    async def test_offline_against_online_response(self, offline_response, online_response):
        assert (
            offline_response == online_response
        ), "MentionableSelect offline response no longer matches online response, please update."

    def test_comp_payload_against_saved(self, comp_payload, saved_comp_payload):
        assert (
            comp_payload == saved_comp_payload
        ), "Saved MentionableSelect payload no longer matches generate, either update or fix."

    def test_comp_payload_typing(self, comp_payload):
        ta = pydantic.TypeAdapter(comp_payloads.MentionableSelectMenu)
        for data in comp_payload:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_offline_response_typing(self, offline_response):
        ta = pydantic.TypeAdapter(comp_payloads.MentionableSelectMenu)
        for data in offline_response:
            ta.validate_python(data["components"][0], extra="forbid", strict=True)

    def test_select_menu_alias(self):
        assert nextcord.MentionableSelectMenu is nextcord.MentionableSelect

    @pytest.mark.parametrize(
        "mentionable_select", [("c", 0), ("p", 0)], ids=fixture_id, indirect=True
    )
    def test_mentionable_select_1_payload_attributes(self, mentionable_select):
        assert isinstance(mentionable_select, nextcord.MentionableSelect)
        assert mentionable_select.id == 10
        assert mentionable_select.custom_id == "test_mentionable_select_1"
        assert mentionable_select.placeholder is MISSING
        assert mentionable_select.default_values is MISSING
        assert mentionable_select.min_values is MISSING
        assert mentionable_select.max_values is MISSING
        assert mentionable_select.disabled is MISSING

    @pytest.mark.parametrize("mentionable_select", [("o", 0)], ids=fixture_id, indirect=True)
    def test_mentionable_select_1_offline_attributes(self, mentionable_select):
        assert isinstance(mentionable_select, nextcord.MentionableSelect)
        assert mentionable_select.id == 10
        assert mentionable_select.custom_id == "test_mentionable_select_1"
        assert mentionable_select.placeholder is MISSING
        assert mentionable_select.default_values is MISSING
        assert mentionable_select.min_values == 1
        assert mentionable_select.max_values == 1
        assert mentionable_select.disabled is MISSING

    @pytest.mark.parametrize(
        "mentionable_select", [("c", 1), ("p", 1), ("o", 1)], ids=fixture_id, indirect=True
    )
    def test_mentionable_select_2_attributes(self, mentionable_select):
        assert isinstance(mentionable_select, nextcord.MentionableSelect)
        assert mentionable_select.id == 20
        assert mentionable_select.custom_id == "test_mentionable_select_2"
        assert mentionable_select.placeholder == "Placeholder text"
        assert mentionable_select.default_values is MISSING
        assert mentionable_select.min_values == 1
        assert mentionable_select.max_values == 1
        assert mentionable_select.disabled is MISSING

    @pytest.mark.parametrize(
        "mentionable_select", [("c", 2), ("p", 2), ("o", 2)], ids=fixture_id, indirect=True
    )
    def test_mentionable_select_3_attributes(self, mentionable_select):
        assert isinstance(mentionable_select, nextcord.MentionableSelect)
        assert mentionable_select.id == 30
        assert mentionable_select.custom_id == "test_mentionable_select_3"
        assert mentionable_select.placeholder is MISSING
        assert mentionable_select.default_values is MISSING
        assert mentionable_select.min_values == 2
        assert mentionable_select.max_values == 3
        assert mentionable_select.disabled is MISSING

    @pytest.mark.parametrize(
        "mentionable_select", [("c", 3), ("p", 3), ("o", 3)], ids=fixture_id, indirect=True
    )
    def test_mentionable_select_4_attributes(self, mentionable_select):
        assert isinstance(mentionable_select, nextcord.MentionableSelect)
        assert mentionable_select.id == 40
        assert mentionable_select.custom_id == "test_mentionable_select_4"
        assert mentionable_select.placeholder is MISSING
        assert mentionable_select.default_values is not MISSING
        assert len(mentionable_select.default_values) == 2
        assert mentionable_select.default_values[0].id == utils.EnvVar.test_user
        assert mentionable_select.default_values[0].type == nextcord.SelectDefaultValueType.user
        assert mentionable_select.default_values[1].id == utils.EnvVar.test_role
        assert mentionable_select.default_values[1].type == nextcord.SelectDefaultValueType.role
        assert mentionable_select.min_values == 1
        assert mentionable_select.max_values == 2
        assert mentionable_select.disabled is MISSING

    @pytest.mark.parametrize(
        "mentionable_select", [("c", 4), ("p", 4), ("o", 4)], ids=fixture_id, indirect=True
    )
    def test_mentionable_select_5_attributes(self, mentionable_select):
        assert isinstance(mentionable_select, nextcord.MentionableSelect)
        assert mentionable_select.id == 50
        assert mentionable_select.custom_id == "test_mentionable_select_5"
        assert mentionable_select.placeholder is MISSING
        assert mentionable_select.default_values is MISSING
        assert mentionable_select.min_values == 1
        assert mentionable_select.max_values == 1
        assert mentionable_select.disabled is True

    def test_mentionable_select_add_default(self):
        select = nextcord.MentionableSelect()
        assert select.default_values is MISSING
        select.add_default_value(utils.EnvVar.test_user, nextcord.SelectDefaultValueType.user)
        assert select.default_values is not MISSING
        assert len(select.default_values) == 1
        assert select.default_values[0].id == utils.EnvVar.test_user
        assert select.default_values[0].type == nextcord.SelectDefaultValueType.user
        select.add_default_value(utils.EnvVar.test_role, nextcord.SelectDefaultValueType.role)
        assert len(select.default_values) == 2
        assert select.default_values[1].id == utils.EnvVar.test_role
        assert select.default_values[1].type == nextcord.SelectDefaultValueType.role


class TestSelectDefaultValues:
    def test_select_default_channel_string(self):
        default = nextcord.SelectDefaultValue(111111, "channel")
        assert default.id == 111111
        assert default.type == nextcord.SelectDefaultValueType.channel

    def test_select_default_channel_enum(self):
        default = nextcord.SelectDefaultValue(111111, nextcord.SelectDefaultValueType.channel)
        assert default.id == 111111
        assert default.type == nextcord.SelectDefaultValueType.channel

    def test_select_default_role_string(self):
        default = nextcord.SelectDefaultValue(111111, "role")
        assert default.id == 111111
        assert default.type == nextcord.SelectDefaultValueType.role

    def test_select_default_role_enum(self):
        default = nextcord.SelectDefaultValue(111111, nextcord.SelectDefaultValueType.role)
        assert default.id == 111111
        assert default.type == nextcord.SelectDefaultValueType.role

    def test_select_default_user_string(self):
        default = nextcord.SelectDefaultValue(111111, "user")
        assert default.id == 111111
        assert default.type == nextcord.SelectDefaultValueType.user

    def test_select_default_user_enum(self):
        default = nextcord.SelectDefaultValue(111111, nextcord.SelectDefaultValueType.user)
        assert default.id == 111111
        assert default.type == nextcord.SelectDefaultValueType.user
