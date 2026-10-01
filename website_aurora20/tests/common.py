from odoo.fields import Command
from odoo.tests import HttpCase

class AuroraCommon(HttpCase):
    """Two websites, three brands and a few products shared by the tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("base.default_website")
        cls.website.write({
            "aurora_enable_brand_pages": True,
            "aurora_enable_quick_view": True,
            "aurora_enable_cart_drawer": True,
            "aurora_b2b_mode": False,
        })
        cls.website_2 = cls.env["website"].create({
            "name": "Aurora Second Website",
            "domain": "http://second.aurora.example.com",
        })
        Brand = cls.env["aurora.product.brand"]
        cls.brand_published = Brand.create({"name": "Aurora Test Northwind", "is_published": True})
        cls.brand_hidden = Brand.create({"name": "Aurora Test Hidden", "is_published": False})
        cls.brand_other_site = Brand.create({
            "name": "Aurora Test Other Site",
            "is_published": True,
            "website_id": cls.website_2.id,
        })
        Product = cls.env["product.template"]
        cls.product_branded = Product.create({
            "name": "Aurora Test Lamp",
            "list_price": 100.0,
            "is_published": True,
            "sale_ok": True,
            "aurora_brand_id": cls.brand_published.id,
        })
        cls.product_plain = Product.create({
            "name": "Aurora Test Mug",
            "list_price": 10.0,
            "is_published": True,
            "sale_ok": True,
        })
        cls.product_unpublished = Product.create({
            "name": "Aurora Test Secret",
            "list_price": 50.0,
            "is_published": False,
            "sale_ok": True,
            "aurora_brand_id": cls.brand_published.id,
        })
        color = cls.env["product.attribute"].create({
            "name": "Aurora Test Color",
            "create_variant": "always",
            "value_ids": [Command.create({"name": "Red"}), Command.create({"name": "Blue"})],
        })
        cls.product_variants = Product.create({
            "name": "Aurora Test Shirt",
            "list_price": 30.0,
            "is_published": True,
            "sale_ok": True,
            "attribute_line_ids": [Command.create({
                "attribute_id": color.id,
                "value_ids": [Command.set(color.value_ids.ids)],
            })],
        })
        cls.portal_user = cls.env["res.users"].create({
            "name": "Aurora Portal Buyer",
            "login": "aurora_portal",
            "password": "aurora_portal",
            "email": "aurora_portal@example.com",
            "group_ids": [Command.set([cls.env.ref("base.group_portal").id])],
        })
