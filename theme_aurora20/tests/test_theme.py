from odoo.tests import HttpCase, tagged

from ..models.theme_aurora20 import AURORA_FOOTERS, AURORA_HEADERS


@tagged("post_install", "-at_install")
class TestAuroraTheme(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("base.default_website")
        cls.theme = cls.env.ref("base.module_theme_aurora20")
        cls.website.theme_id = cls.theme
        cls.theme.with_context(apply_new_theme=True)._theme_load(cls.website)
        cls.other_website = cls.env["website"].create({
            "name": "Aurora no-theme website",
            "domain": "http://other.aurora.example.com",
        })

    def _views(self, website, key):
        return self.env["ir.ui.view"].with_context(active_test=False).search([
            ("key", "=", key), ("website_id", "=", website.id),
        ])

    def test_theme_load_defaults(self):
        self.assertTrue(self._views(self.website, "theme_aurora20.template_header_classic").active)
        self.assertTrue(self._views(self.website, "theme_aurora20.template_footer_store").active)
        assets = self.env["ir.asset"].search([
            ("key", "like", "theme_aurora20."), ("website_id", "=", self.website.id),
        ])
        self.assertEqual(len(assets), 3)

    def test_theme_isolated_per_website(self):
        self.assertFalse(self._views(self.other_website, "theme_aurora20.template_header_classic"))
        res = self.url_open("/", headers={"Host": "other.aurora.example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("o_aurora_header", res.text)
        self.assertIn("o_aurora_header", self.url_open("/").text)

    def test_every_header_and_footer_renders(self):
        utils = self.env["theme.utils"].with_context(website_id=self.website.id)
        for header, footer in zip(AURORA_HEADERS, AURORA_FOOTERS):
            with self.subTest(header=header, footer=footer):
                utils.enable_view(header)
                utils.enable_view(footer)
                active_headers = [h for h in AURORA_HEADERS if self._views(self.website, h).active]
                self.assertEqual(active_headers, [header], "only one Aurora header at a time")
                res = self.url_open("/shop")
                self.assertEqual(res.status_code, 200)
                header_class = "o_aurora_header_" + header.rsplit("_", 1)[-1]
                self.assertIn(header_class, res.text)
                self.assertIn("o_aurora_footer", res.text)
                # eCommerce and account entries are present in every header
                self.assertIn('href="/shop/cart"', res.text)
                self.assertIn("o_header_mobile", res.text)

    def test_switch_back_to_odoo_header(self):
        utils = self.env["theme.utils"].with_context(website_id=self.website.id)
        utils.enable_view("website.template_header_default")
        self.assertFalse(self._views(self.website, "theme_aurora20.template_header_classic").active)
        self.assertNotIn("o_aurora_header", self.url_open("/").text)

    def test_frontend_assets_compile(self):
        res = self.url_open("/")
        self.assertEqual(res.status_code, 200)
        css_url = next(
            part.split('"')[0]
            for part in res.text.split('href="')[1:]
            if "web.assets_frontend" in part.split('"')[0] and part.split('"')[0].endswith(".css")
        )
        css = self.url_open(css_url).text
        self.assertIn("o_aurora_header_split", css)
        self.assertIn("#4F46E5".lower(), css.lower())
