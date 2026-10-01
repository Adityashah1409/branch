from odoo.tests import TransactionCase, tagged

from odoo.modules import Manifest


@tagged("post_install", "-at_install")
class TestHomepageDesigns(TransactionCase):

    def test_ten_designs_generated_and_render(self):
        designs = Manifest.for_addon("website_aurora20")["new_page_templates"]["aurora_home"]
        self.assertGreaterEqual(len(designs), 10)
        website = self.env.ref("base.default_website").with_context(inherit_branding=False)
        for name in designs:
            with self.subTest(design=name):
                key = "website_aurora20.new_page_template_sections_aurora_home_%s" % name
                view = self.env["ir.ui.view"].search([("key", "=", key)])
                self.assertTrue(view, key)
                html = str(website._render_template(key))
                self.assertIn('id="wrap"', html)
                # One top-level block per snippet of the design.
                prefix = 'data-snippet="new_page_template_aurora_home_%s_' % name
                self.assertEqual(html.count(prefix) + html.count('data-snippet="s_dynamic_snippet_products"'),
                                 len(designs[name]))

    def test_group_listed(self):
        groups = str(self.env.ref("base.default_website")._render_template("website.new_page_template_groups"))
        self.assertIn('id="aurora_home"', groups)
