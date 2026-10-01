import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

const UNITS = { days: 86400, hours: 3600, minutes: 60, seconds: 1 };

/** Live countdown of the "Countdown Banner" building block. */
export class AuroraCountdown extends Interaction {
    static selector = ".s_aurora_countdown";

    setup() {
        const end = this.el.dataset.end ? new Date(this.el.dataset.end) : null;
        if (end && !Number.isNaN(end.getTime())) {
            this.end = end;
        } else {
            // No (valid) end date: count down to the next midnight.
            this.end = new Date();
            this.end.setHours(24, 0, 0, 0);
        }
        this.valueEls = this.el.querySelectorAll("[data-unit]");
    }

    start() {
        const previous = [...this.valueEls].map((el) => el.textContent);
        this.registerCleanup(() => this.valueEls.forEach((el, i) => (el.textContent = previous[i])));
        this.tick();
        this.setSafeInterval(() => this.tick(), 1000);
    }

    tick() {
        let remaining = Math.max(0, Math.floor((this.end - Date.now()) / 1000));
        for (const el of this.valueEls) {
            const size = UNITS[el.dataset.unit] || 1;
            const value = Math.floor(remaining / size);
            remaining -= value * size;
            el.textContent = String(value).padStart(2, "0");
        }
    }
}

registry.category("public.interactions").add("website_aurora20.countdown", AuroraCountdown);
