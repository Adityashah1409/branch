import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("website_aurora20_quick_view_drawer", {
    steps: () => [
        {
            content: "Open the quick view of the product",
            trigger: ".oe_product_cart:contains('Aurora Tour Product')",
            run: "hover && click .oe_product_cart:contains('Aurora Tour Product') .o_aurora_quick_view_btn",
        },
        {
            content: "The dialog shows the product",
            trigger: "#o_aurora_quick_view.show .o_aurora_qv_name:contains('Aurora Tour Product')",
        },
        {
            content: "Add one more",
            trigger: "#o_aurora_quick_view .o_aurora_qty_plus",
            run: "click",
        },
        {
            content: "Add to cart",
            trigger: "#o_aurora_quick_view button[name=add_to_cart]",
            run: "click",
        },
        {
            content: "The cart drawer opens with the product",
            trigger: "#o_aurora_cart_drawer.show .o_aurora_cart_line:contains('Aurora Tour Product')",
        },
        {
            content: "The quantity is 2",
            trigger: "#o_aurora_cart_drawer .o_aurora_cart_qty_input:value(2)",
        },
        {
            content: "Increase the quantity in the drawer",
            trigger: "#o_aurora_cart_drawer .o_aurora_cart_qty[data-delta='1']",
            run: "click",
        },
        {
            content: "The quantity is 3",
            trigger: "#o_aurora_cart_drawer .o_aurora_cart_qty_input:value(3)",
        },
        {
            content: "Remove the line",
            trigger: "#o_aurora_cart_drawer .o_aurora_cart_remove",
            run: "click",
        },
        {
            content: "The cart is empty",
            trigger: "#o_aurora_cart_drawer:not(:has(.o_aurora_cart_line))",
        },
    ],
});
