from odoo.tests import tagged
from odoo.tests.common import JsonRpcException

from .common import AuroraCommon


@tagged("post_install", "-at_install")
class TestStorefrontRoutes(AuroraCommon):

    def test_quick_view(self):
        result = self.make_jsonrpc_request("/aurora/quick_view", {
            "product_template_id": self.product_branded.id,
        })
        self.assertEqual(result["name"], "Aurora Test Lamp")
        self.assertIn('name="add_to_cart"', result["html"])
        self.assertIn("Aurora Test Northwind", result["html"])

    def test_quick_view_refuses_unpublished_and_bad_input(self):
        for params in (
            {"product_template_id": self.product_unpublished.id},
            {"product_template_id": "abc"},
            {"product_template_id": self.product_plain.id, "combination": ["x"]},
        ):
            with self.subTest(params=params), self.assertRaises(JsonRpcException):
                self.make_jsonrpc_request("/aurora/quick_view", params)

    def test_quick_view_disabled(self):
        self.website.aurora_enable_quick_view = False
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request("/aurora/quick_view", {"product_template_id": self.product_plain.id})

    def test_quick_view_combination(self):
        """The picked variant is shown; values of other products are ignored."""
        ptavs = self.product_variants.valid_product_template_attribute_line_ids.product_template_value_ids
        blue = ptavs.filtered(lambda v: v.name == "Blue")
        result = self.make_jsonrpc_request("/aurora/quick_view", {
            "product_template_id": self.product_variants.id,
            "combination": [blue.id],
        })
        self.assertIn("Blue", result["html"])
        self.assertIn('data-product-id="%s"' % blue.ptav_product_variant_ids.id, result["html"])
        # Foreign values are dropped, the dialog still renders.
        result = self.make_jsonrpc_request("/aurora/quick_view", {
            "product_template_id": self.product_variants.id,
            "combination": [999999],
        })
        self.assertIn("Aurora Test Shirt", result["html"])

    def test_cart_drawer(self):
        result = self.make_jsonrpc_request("/aurora/cart/drawer")
        self.assertEqual(result["cart_quantity"], 0)
        self.make_jsonrpc_request("/shop/cart/add", {
            "product_template_id": self.product_plain.id,
            "product_id": self.product_plain.product_variant_id.id,
            "quantity": 2,
        })
        result = self.make_jsonrpc_request("/aurora/cart/drawer")
        self.assertEqual(result["cart_quantity"], 2)
        self.assertIn("o_aurora_cart_line", result["html"])
        self.assertIn("Aurora Test Mug", result["html"])

    def test_layout_renders_containers(self):
        res = self.url_open("/shop")
        self.assertIn('id="o_aurora_quick_view"', res.text)
        self.assertIn('id="o_aurora_cart_drawer"', res.text)
        self.assertIn("o_aurora_quick_view_btn", res.text)
        self.website.write({"aurora_enable_quick_view": False, "aurora_enable_cart_drawer": False})
        res = self.url_open("/shop")
        self.assertNotIn('id="o_aurora_quick_view"', res.text)
        self.assertNotIn('id="o_aurora_cart_drawer"', res.text)
        self.assertNotIn("o_aurora_quick_view_btn", res.text)

    def test_announcement_bar(self):
        self.website.write({"aurora_announcement_enabled": True, "aurora_announcement_text": "Hello Aurora shoppers"})
        self.assertIn("Hello Aurora shoppers", self.url_open("/").text)
        self.website.aurora_announcement_enabled = False
        self.assertNotIn("Hello Aurora shoppers", self.url_open("/").text)
