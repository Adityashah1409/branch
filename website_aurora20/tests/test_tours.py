from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestStorefrontTours(HttpCase):

    def test_quick_view_and_cart_drawer(self):
        self.env["product.template"].create({
            "name": "Aurora Tour Product",
            "list_price": 42.0,
            "is_published": True,
            "sale_ok": True,
            "website_sequence": 1,
        })
        self.env.ref("base.default_website").write({
            "aurora_enable_quick_view": True,
            "aurora_enable_cart_drawer": True,
            "aurora_cart_drawer_auto_open": True,
        })
        self.start_tour("/shop?search=Aurora Tour Product", "website_aurora20_quick_view_drawer")
