# M08 — Inventory & asset register

**Depends on:** M00 (M06 for cost/payment links, M03 for cohort assignment). **Attach with:** `01_MASTER_CONTEXT.md`, `PROGRESS.md`.

## Goal
Know where every kit, laptop and box of batteries is, who has it, its condition, and what it cost —
with stock calculated from recorded movements, never from overwritten quantities.

## Scope
**In:** categories, stock items (quantity-based) and serialized assets, kit definitions and components, locations
(center, schools, storage), opening balances, goods receipts, reservations, checkout/return (incl. partial and missing
parts), transfers, consumption, stock counts and adjustments, maintenance/repairs/disposal, minimum-stock alerts,
printable asset register, cost links to purchases (M09/M06).
**Out:** supplier bills and payments themselves (M09/M06).

## Data model (`apps/api/app/modules/inventory/models.py`)
- `inventory_category` (name, type: kit | electronics | furniture | consumable | other, useful_life_months nullable — set by finance, used by M12 for estimated book value)
- `stock_item` (sku unique, name, category_id, unit, tracking: quantity | serialized, min_stock, default_location_id)
- `asset` (stock_item_id, serial_no/asset_tag unique, purchase_date, purchase_cost, supplier_party_id, warranty_until, condition: new | good | worn | damaged | lost | disposed, current_location_id, assigned_to_type: staff | cohort | location, assigned_to_id)
- `kit_definition` (stock_item_id for the kit, version) + `kit_component` (kit_definition_id, component_item_id, quantity)
- `kit_instance` (asset_id of the kit, kit_definition_id, completeness: complete | incomplete, missing_parts jsonb)
- `stock_movement` (item_id, asset_id nullable, type: opening | receipt | transfer_out | transfer_in | issue | return | consume | adjust | assemble | disassemble | dispose | reversal,
  qty (signed), from_location_id, to_location_id, ref_type (purchase_receipt, cohort, staff, count), ref_id, reason, reverses_movement_id, posted_by, posted_at)
- `reservation` (item/asset, qty, for_type: cohort | event | staff, for_id, from, to, status)
- `purchase_receipt` (supplier_party_id, received_at, received_by, supplier_bill_document_id nullable, lines → stock_movement receipt)
- `stock_count` (location_id, counted_at, status: open | posted) + `stock_count_line` (item_id, expected, counted, adjustment_movement_id)
- `maintenance_record` (asset_id, type: inspection | repair | warranty, scheduled_for, done_at, cost, note, document_id nullable)

## Rules
- On-hand per item/location = sum of posted movements. No direct quantity edits.
- Opening inventory is a dated `opening` movement.
- Assembling a kit consumes its components from available stock (components inside a kit are not separately available); disassembling returns them.
- Reservation ≠ checkout ≠ return; partial returns and missing parts recorded; missing parts make the kit `incomplete`.
- Negative available stock is blocked unless an admin enables a per-item exception (audited).
- Posted movements are never deleted; corrections use `reversal` movements.
- Receiving goods links to the supplier bill (M09) but is not a payment and does not create a second cost.
- Equipment acquisition is an asset (capitalised value) — reporting must not double-count it as operating expense.
- Instructors can request equipment and acknowledge assignment/return; operations manage stock; finance sees costs; admins manage permissions.

## API
`/inventory/categories|items|assets|kits`, `/inventory/movements` (post, reverse), `/inventory/receipts`, `/inventory/reservations`,
`/inventory/checkouts` (issue/return incl. partial), `/inventory/transfers`, `/inventory/counts` (open, enter, post), `/inventory/maintenance`,
`/inventory/alerts`, `GET /inventory/register.pdf|csv`, `/my/equipment` (instructor).

## Screens
Items & assets register (filters, search), asset detail (history timeline), kit builder, receive goods, checkout/return wizard with missing-parts checklist,
transfer between locations (center ↔ schools), stock count sheet, maintenance calendar, low-stock alerts, instructor "my equipment".

## Audit actions
`inventory.item_created|edited`, `movement.posted|reversed`, `receipt.posted`, `reservation.created|cancelled`, `checkout.issued|returned|partial`,
`transfer.posted`, `count.posted`, `asset.condition_changed|disposed`, `maintenance.recorded`, `stock_exception.enabled`, `register.exported`.

## Sub-steps
- **A.** Schema + migration; items, assets, categories, movements engine (on-hand calc), opening balances + tests.
- **B.** Kits (assemble/disassemble), receipts, reservations, checkout/return/partial, transfers + tests.
- **C.** Counts/adjustments, maintenance, alerts job, register PDF/CSV, screens.

## Acceptance tests
- Purchase received → assigned to cohort → transferred to school → partially returned with 2 missing parts → adjusted with reason: stock and kit counts reconcile; components never counted twice.
- Attempted negative stock blocked; reversal keeps history.
