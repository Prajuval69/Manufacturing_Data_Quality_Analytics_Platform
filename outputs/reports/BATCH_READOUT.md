# PackRight synthetic batch readout

Orders: 4,599; production: 58,834,906 EA; latest observed inventory: 2,476,422 EA.

On-time delivery: 48.64%; open/in-review exceptions: 3,601; incoming DQ score: 99.3191/100.

Blocking checks quarantine invalid rows. Anomalies remain visible and can inflate quantities; join data_quality_flags.csv by table and record key to inspect or exclude them in reporting. The DQ score is a weighted check pass rate, not the percentage of trusted records.

Most frequent failed rules:

- fact_sales_order_line.order_id.reference: 407 of 5030 checks (8.09%); Critical.
- fact_shipment.order_id.reference: 402 of 5030 checks (7.99%); Critical.
- fact_production.material_id.reference: 244 of 8048 checks (3.03%); Critical.
- fact_production.product_id.reference: 197 of 8048 checks (2.45%); Critical.
- fact_sales_order_line.order_id.order_line: 172 of 5030 checks (3.42%); High.
- fact_sales_order.product_id.reference: 150 of 5030 checks (2.98%); Critical.
- fact_sales_order_line.product_id.reference: 150 of 5030 checks (2.98%); Critical.
- fact_inventory.product_id.reference: 111 of 5030 checks (2.21%); Critical.
- fact_production.uom.canonical_unit: 97 of 8048 checks (1.21%); Medium.
- fact_production.production_date.not_null: 96 of 8048 checks (1.19%); High.
- fact_inventory.uom.canonical_unit: 61 of 5030 checks (1.21%); Medium.
- fact_sales_order.uom.canonical_unit: 60 of 5030 checks (1.19%); Medium.
- fact_sales_order_line.uom.canonical_unit: 60 of 5030 checks (1.19%); Medium.
- fact_shipment.ship_date.not_null: 60 of 5030 checks (1.19%); High.
- fact_sales_order.order_date.not_null: 59 of 5030 checks (1.17%); High.
