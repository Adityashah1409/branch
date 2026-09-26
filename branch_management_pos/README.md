# Multi Branch Management - Point of Sale (`branch_management_pos`)

Branch integration for the Odoo 20 Point of Sale. Depends on
`branch_management_account` and `point_of_sale` (which, in Odoo 20, does not
depend on `stock`; see `branch_management_pos_stock`).

## Business rule: Branch -> Shop -> sessions, orders, accounting

| Model | `branch_id` | How |
|---|---|---|
| `pos.config` (shop) | `res.branch.mixin` | chosen on the shop (form and PoS settings); same company, allowed branch; cannot change while a session is in progress |
| `pos.session` | mixin, stored compute, read-only | shop's branch when the session is created (depends on `config_id` only: history is kept when the shop moves) |
| `pos.order` | mixin, stored compute, read-only | shop's branch (`config_id`); kept when an order is detached from its session |
| `pos.order.line`, `pos.payment` | stored related | order's branch |
| `report.pos.order` | SQL column | `pos_order.branch_id` (`_select`) |

## Accounting created in the shop's branch

| Document | Hook (Odoo 20) |
|---|---|
| Invoice of an order | `pos.order._prepare_invoice_vals` (orders of several branches cannot be invoiced together) |
| Session closing entry | `pos.session._prepare_session_move_vals` |
| Reversal of the closing entry (invoice after closing) | `account.move.create`: `reversed_pos_order_id` / `pos_session_ids` values |
| Bank payments | `account.payment.create`: `pos_session_id` value |
| Cash statement lines (sales, cash in/out, cash differences) | `account.bank.statement.line.create`: `pos_session_id` value |
| Bank difference entries and anything else created while closing | `pos.session._validate_session_accounting`, `_handle_bank_payment_method_difference`, `_handle_cash_statement_entries` set a context key read by the creates above |

These flows run in `sudo()`, where the mixin default would be the working
branch of the user closing the session: the shop's branch is used instead.
Shops without branch produce entries without branch.

## Validations

* journals of the shop (`journal_id`, `closing_journal_id`, payment methods'
  journals) dedicated to another branch are refused;
* shops can only share open orders (`trusted_config_ids`) with shops of the
  same branch (the orders are pushed to the other shop's sessions).

## Security (`security/ir.access.csv`)

Group-less restrictions on `pos.config`, `pos.session`, `pos.order`,
`pos.order.line`, `pos.payment` and `report.pos.order`: records without branch or
of an allowed branch. A cashier opens and uses the shops of their allowed
branches; shops without branch stay visible to everybody.

## Views

Branch on the shop form / list / search and in the PoS settings; on session,
order and payment lists, forms and searches (Current Branch filter, group by
Branch); PoS order analysis grouped by branch; *Point of Sale Orders* smart
button on the branch form.

## Limitations

* The branch column is not added to `sale.report` rows coming from PoS orders
  (`pos_sale`): they show no branch there.
* Stock valuation entries of PoS pickings follow the stock / stock_account
  flows (no branch bridge for `stock_account` yet).
