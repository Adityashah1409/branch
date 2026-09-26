import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("branch_selector_switch", {
    steps: () => [
        {
            content: "The working branch is the default branch",
            trigger: ".o_branch_selector_name:contains(Ahmedabad)",
        },
        {
            content: "Open the branch selector",
            trigger: ".o_branch_selector",
            run: "click",
        },
        {
            content: "Only valid branches are listed",
            trigger: ".o_branch_selector_dropdown:not(:has(.o_branch_selector_item:contains(Mumbai)))",
        },
        {
            content: "Switch to Surat",
            trigger: ".o_branch_selector_item:contains(Surat)",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Surat is the working branch after the reload",
            trigger: ".o_branch_selector_name:contains(Surat)",
        },
        {
            content: "Reload the browser (new page load, same session cookie)",
            trigger: ".o_branch_selector_name:contains(Surat)",
            run: () => window.location.reload(),
            expectUnloadPage: true,
        },
        {
            content: "The working branch survived the page load",
            trigger: ".o_branch_selector_name:contains(Surat)",
        },
    ],
});
