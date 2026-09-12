# SPDX-License-Identifier: MIT

import unittest

from nextcord import ui


class CustomIDTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_ids_are_rejected_at_construction(self):
        for factory in self.factories():
            for value in (123, False, b"id", [], {}, object()):
                with (
                    self.subTest(factory=factory, value=value),
                    self.assertRaisesRegex(TypeError, "custom_id"),
                ):
                    factory(custom_id=value)

    async def test_invalid_assignment_preserves_previous_id(self):
        for factory in self.factories():
            for value in (123, False, b"id", [], {}, object()):
                obj = factory(custom_id="original")
                with self.subTest(factory=factory, value=value):
                    with self.assertRaisesRegex(TypeError, "custom_id"):
                        obj.custom_id = value
                    self.assertEqual(obj.custom_id, "original")

    async def test_explicit_and_generated_ids(self):
        for factory in self.factories():
            with self.subTest(factory=factory):
                self.assertEqual(factory(custom_id="stable").custom_id, "stable")
                obj = factory()
                self.assertIsInstance(obj.custom_id, str)
                self.assertEqual(len(obj.custom_id), 32)
                obj.custom_id = "replacement"
                self.assertEqual(obj.custom_id, "replacement")

    async def test_link_button_and_select_none_defaults(self):
        self.assertIsNone(ui.Button(url="https://example.com").custom_id)
        for factory in (
            ui.Button,
            ui.StringSelect,
            ui.UserSelect,
            ui.RoleSelect,
            ui.MentionableSelect,
            ui.ChannelSelect,
        ):
            with self.subTest(factory=factory):
                self.assertIsInstance(factory(custom_id=None).custom_id, str)

    async def test_decorator_defaults_generate_ids(self):
        for decorate in (
            ui.button,
            ui.string_select,
            ui.user_select,
            ui.role_select,
            ui.mentionable_select,
            ui.channel_select,
        ):

            async def callback(self, item, interaction):
                pass

            with self.subTest(decorate=decorate):
                view_type = type("DecoratedView", (ui.View,), {"item": decorate()(callback)})
                view = view_type()
                self.assertIsInstance(view.children[0].custom_id, str)
                self.assertFalse(view.children[0]._provided_custom_id)

    async def test_required_ids_reject_none(self):
        for factory in (
            lambda **kw: ui.TextInput(label="Label", **kw),
            lambda **kw: ui.Modal("Title", **kw),
        ):
            with self.subTest(factory=factory):
                with self.assertRaisesRegex(TypeError, "custom_id"):
                    factory(custom_id=None)
                obj = factory(custom_id="original")
                with self.assertRaisesRegex(TypeError, "custom_id"):
                    obj.custom_id = None
                self.assertEqual(obj.custom_id, "original")

    async def test_component_reconstruction_validates_ids(self):
        for factory in self.factories()[:6]:
            obj = factory(custom_id="original")
            with self.subTest(factory=factory):
                component = type(obj._underlying).from_dict(obj.to_component_dict())
                component.custom_id = 123
                with self.assertRaisesRegex(TypeError, "custom_id"):
                    factory.from_component(component)

    @staticmethod
    def factories():
        return (
            ui.Button,
            ui.StringSelect,
            ui.UserSelect,
            ui.RoleSelect,
            ui.MentionableSelect,
            ui.ChannelSelect,
            lambda **kw: ui.TextInput(label="Label", **kw),
            lambda **kw: ui.Modal("Title", **kw),
        )
