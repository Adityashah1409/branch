from odoo.tests import TransactionCase, tagged

from ..models.website import AURORA_DEFAULTS


@tagged("post_install", "-at_install")
class TestStorefrontSettings(TransactionCase):

    def test_settings_are_per_website(self):
        website_1 = self.env.ref("base.default_website")
        website_2 = self.env["website"].create({"name": "Aurora settings site"})
        website_1.aurora_product_card_style = "minimal"
        website_1.aurora_b2b_mode = True
        self.assertEqual(website_2.aurora_product_card_style, "classic")
        self.assertFalse(website_2.aurora_b2b_mode)

    def test_reset_settings(self):
        website = self.env["website"].create({"name": "Aurora reset site"})
        website.write({
            "aurora_enable_quick_view": False,
            "aurora_product_card_style": "compact",
            "aurora_b2b_mode": True,
            "aurora_announcement_text": "Custom",
        })
        product_count = self.env["product.template"].search_count([])
        website.action_aurora_reset_settings()
        for field, value in AURORA_DEFAULTS.items():
            self.assertEqual(website[field], value, field)
        self.assertEqual(website.aurora_announcement_text, "Free shipping on orders over 50")
        self.assertEqual(self.env["product.template"].search_count([]), product_count)
