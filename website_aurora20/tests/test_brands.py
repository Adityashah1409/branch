from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import AuroraCommon


@tagged("post_install", "-at_install")
class TestBrands(AuroraCommon):

    def test_public_brand_access_rules(self):
        Brand = self.env["aurora.product.brand"].with_user(self.website.user_id)
        visible = Brand.search([("name", "like", "Aurora Test")])
        self.assertIn(self.brand_published, visible)
        self.assertNotIn(self.brand_hidden, visible)

    def test_brands_page_lists_published_brands_of_this_website(self):
        res = self.url_open("/brands")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Aurora Test Northwind", res.text)
        self.assertNotIn("Aurora Test Hidden", res.text)
        self.assertNotIn("Aurora Test Other Site", res.text)

    def test_brands_page_search(self):
        res = self.url_open("/brands?search=Northwind")
        self.assertIn("Aurora Test Northwind", res.text)
        res = self.url_open("/brands?search=zzz-nothing")
        self.assertNotIn("Aurora Test Northwind", res.text)

    def test_brand_page(self):
        res = self.url_open(self.brand_published.website_url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Aurora Test Lamp", res.text)
        self.assertNotIn("Aurora Test Secret", res.text)  # unpublished product

    def test_brand_page_not_found(self):
        self.assertEqual(self.url_open(self.brand_hidden.website_url).status_code, 404)
        self.assertEqual(self.url_open(self.brand_other_site.website_url).status_code, 404)

    def test_brand_pages_disabled(self):
        self.website.aurora_enable_brand_pages = False
        self.assertEqual(self.url_open("/brands").status_code, 404)
        self.assertEqual(self.url_open(self.brand_published.website_url).status_code, 404)

    def test_brand_pages_need_ecommerce_access(self):
        self.website.ecommerce_access = "logged_in"
        res = self.url_open("/brands", allow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertIn("/web/login", res.headers["Location"])

    def test_shop_brand_filter(self):
        res = self.url_open("/shop?brand=%s" % self.brand_published.id)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Aurora Test Lamp", res.text)
        self.assertNotIn("Aurora Test Mug", res.text)
        # an invalid value is ignored
        res = self.url_open("/shop?brand=abc")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Aurora Test Mug", res.text)

    def test_product_search_finds_brand_name(self):
        res = self.url_open("/shop?search=Northwind")
        self.assertIn("Aurora Test Lamp", res.text)

    def test_website_search_returns_brands(self):
        website = self.website.with_context(website_id=self.website.id)
        options = {
            "displayDescription": False, "displayDetail": False, "displayExtraDetail": False,
            "displayExtraLink": False, "displayImage": True, "allowFuzzy": False,
            "display_currency": website.currency_id,
        }
        details = website._search_get_details("all", "name asc", options)
        self.assertIn("aurora.product.brand", [d["model"] for d in details])
        self.website.aurora_enable_brand_pages = False
        details = website._search_get_details("all", "name asc", options)
        self.assertNotIn("aurora.product.brand", [d["model"] for d in details])

    def test_brands_snippet(self):
        result = self.make_jsonrpc_request("/aurora/brands/snippet", {"limit": 500})
        self.assertIn("Aurora Test Northwind", result["html"])
        self.assertNotIn("Aurora Test Hidden", result["html"])
        result = self.make_jsonrpc_request("/aurora/brands/snippet", {"featured_only": True})
        self.assertNotIn("Aurora Test Northwind", result["html"])

    def test_brand_name_unique_per_website(self):
        with self.assertRaises(IntegrityError), self.cr.savepoint(), mute_logger("odoo.sql_db"):
            self.env["aurora.product.brand"].create({
                "name": "Aurora Test Other Site", "website_id": self.website_2.id,
            })

    def test_product_count(self):
        self.assertEqual(self.brand_published.product_count, 2)
        self.assertEqual(self.brand_published._get_published_product_count(self.website), 1)
