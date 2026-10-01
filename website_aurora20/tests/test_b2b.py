from odoo.tests import tagged
from odoo.tests.common import JsonRpcException

from odoo.addons.website_sale.tests.common import MockRequest

from .common import AuroraCommon


@tagged("post_install", "-at_install")
class TestB2BMode(AuroraCommon):
    """B2B mode is enforced by the server, not only hidden in the pages."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website.write({
            "aurora_b2b_mode": True,
            "aurora_b2b_hide_prices": True,
            "aurora_b2b_hide_add_to_cart": True,
        })

    def _env_as(self, user, website=None):
        website = website or self.website
        return self.env(user=user, context=dict(self.env.context, website_id=website.id))

    def _combination_info(self, env, product):
        website = env["website"].browse(env.context["website_id"])
        with MockRequest(env, website=website):
            return env["product.template"].browse(product.id)._get_combination_info()

    def test_guest_combination_info_hides_prices(self):
        env = self._env_as(self.website.user_id)
        info = self._combination_info(env, self.product_plain)
        self.assertTrue(info["hide_price"])
        self.assertTrue(info["prevent_sale"])
        self.assertEqual(info["price"], 0.0)
        self.assertEqual(info["list_price"], 0.0)
        self.assertNotIn("base_unit_price", info)

    def test_guest_sales_prices_hidden(self):
        env = self._env_as(self.website.user_id)
        website = env["website"].browse(self.website.id)
        products = env["product.template"].browse(self.product_plain.id)
        prices = products._get_sales_prices(website.pricelist_id.sudo(), env["account.fiscal.position"], website)
        self.assertEqual(prices[self.product_plain.id], {"price_reduce": 0.0})

    def test_guest_cannot_add_to_cart_model(self):
        env = self._env_as(self.website.user_id)
        variant = env["product.product"].browse(self.product_plain.product_variant_id.id)
        self.assertFalse(variant._is_add_to_cart_allowed())
        self.assertFalse(env["product.template"].browse(self.product_plain.id)._website_show_quick_add())

    def test_signed_in_customer_can_buy(self):
        env = self._env_as(self.portal_user)
        info = self._combination_info(env, self.product_plain)
        self.assertFalse(info.get("hide_price"))
        self.assertEqual(info["price"], 10.0)
        variant = env["product.product"].browse(self.product_plain.product_variant_id.id)
        self.assertTrue(variant._is_add_to_cart_allowed())

    def test_prices_visible_when_only_cart_hidden(self):
        self.website.aurora_b2b_hide_prices = False
        env = self._env_as(self.website.user_id)
        info = self._combination_info(env, self.product_plain)
        self.assertFalse(info.get("hide_price"))
        self.assertEqual(info["price"], 10.0)
        self.assertTrue(info["prevent_sale"])

    def test_b2b_off_on_other_website(self):
        env = self._env_as(self.website_2.user_id, self.website_2)
        info = self._combination_info(env, self.product_plain)
        self.assertFalse(info.get("hide_price"))

    def test_guest_add_to_cart_request_refused(self):
        """A guest calling the cart route directly gets no order line."""
        self.authenticate(None, None)
        try:
            self.make_jsonrpc_request("/shop/cart/add", {
                "product_template_id": self.product_plain.id,
                "product_id": self.product_plain.product_variant_id.id,
                "quantity": 1,
            })
        except JsonRpcException:
            pass  # refused with an error: fine
        lines = self.env["sale.order.line"].sudo().search([
            ("product_id", "=", self.product_plain.product_variant_id.id),
        ])
        self.assertFalse(lines)

    def test_guest_pages_hide_prices(self):
        self.authenticate(None, None)
        res = self.url_open(self.product_plain.website_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("o_aurora_b2b_notice", res.text)
        # Same as Odoo's own "prevent sale": the button is hidden, and the
        # server refuses the order line anyway (see the test above).
        self.assertRegex(res.text, r'id="add_to_cart_wrap"\s+class="d-none')
        res = self.url_open("/shop")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Sign in to see the price", res.text)
