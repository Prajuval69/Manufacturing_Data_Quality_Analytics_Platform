# Executed rule catalog

Definitions are in config/dq_rules.json. Raw-phase checks measure incoming uniqueness and canonical formatting. Other checks run on standardized rows, against accepted parents.

|Rule ID|Dimension|Severity|Phase|Blocking|Logic parameters|
|---|---|---|---|---|---|
|dim_customer.customer_id.not_null|completeness|High|cleaned|True|{}|
|dim_customer.customer_name.not_null|completeness|High|cleaned|True|{}|
|dim_customer.country.not_null|completeness|High|cleaned|True|{}|
|dim_customer.customer_id.unique|uniqueness|High|raw|True|{}|
|dim_customer.customer_id.pattern|validity|High|cleaned|True|{"pattern": "C[0-9]{5}"}|
|dim_customer.customer_id.reference|referential_integrity|Critical|cleaned|True|{"reference": true, "target": "dim_customer"}|
|dim_customer.country.allowed|validity|High|cleaned|True|{"values": ["IN", "US", "DE", "SG", "AE"]}|
|dim_customer.customer_name.canonical_label|consistency|Medium|raw|False|{"key": "customer_id"}|
|dim_product.product_id.not_null|completeness|High|cleaned|True|{}|
|dim_product.product_description.not_null|completeness|High|cleaned|True|{}|
|dim_product.category.not_null|completeness|High|cleaned|True|{}|
|dim_product.uom.not_null|completeness|High|cleaned|True|{}|
|dim_product.supplier_id.not_null|completeness|High|cleaned|True|{}|
|dim_product.product_id.unique|uniqueness|High|raw|True|{}|
|dim_product.product_id.pattern|validity|High|cleaned|True|{"pattern": "P[0-9]{5}"}|
|dim_product.product_id.reference|referential_integrity|Critical|cleaned|True|{"reference": true, "target": "dim_product"}|
|dim_product.supplier_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_supplier"}|
|dim_product.uom.allowed|validity|Medium|cleaned|True|{"values": ["EA", "KG", "L"]}|
|dim_product.uom.canonical_unit|consistency|Medium|raw|False|{}|
|dim_product.category.allowed|validity|High|cleaned|True|{"values": ["FIBER PACKAGING", "METAL CONTAINERS", "POLYMER PACKAGING", "INDUSTRIAL DRUMS", "INTERMEDIATE BULK CONTAINERS"]}|
|dim_product.product_description.canonical_label|consistency|Medium|raw|False|{"key": "product_id"}|
|dim_facility.facility_id.not_null|completeness|High|cleaned|True|{}|
|dim_facility.facility_name.not_null|completeness|High|cleaned|True|{}|
|dim_facility.city.not_null|completeness|High|cleaned|True|{}|
|dim_facility.facility_id.unique|uniqueness|High|raw|True|{}|
|dim_facility.facility_id.pattern|validity|High|cleaned|True|{"pattern": "F[0-9]{3}"}|
|dim_facility.facility_id.reference|referential_integrity|Critical|cleaned|True|{"reference": true, "target": "dim_facility"}|
|dim_facility.facility_name.canonical_label|consistency|Medium|raw|False|{"key": "facility_id"}|
|dim_supplier.supplier_id.not_null|completeness|High|cleaned|True|{}|
|dim_supplier.supplier_name.not_null|completeness|High|cleaned|True|{}|
|dim_supplier.country.not_null|completeness|High|cleaned|True|{}|
|dim_supplier.supplier_id.unique|uniqueness|High|raw|True|{}|
|dim_supplier.supplier_id.pattern|validity|High|cleaned|True|{"pattern": "S[0-9]{5}"}|
|dim_supplier.supplier_id.reference|referential_integrity|Critical|cleaned|True|{"reference": true, "target": "dim_supplier"}|
|dim_supplier.country.allowed|validity|High|cleaned|True|{"values": ["IN", "US", "DE", "SG", "AE"]}|
|dim_supplier.supplier_name.canonical_label|consistency|Medium|raw|False|{"key": "supplier_id"}|
|dim_material.material_id.not_null|completeness|High|cleaned|True|{}|
|dim_material.material_name.not_null|completeness|High|cleaned|True|{}|
|dim_material.supplier_id.not_null|completeness|High|cleaned|True|{}|
|dim_material.uom.not_null|completeness|High|cleaned|True|{}|
|dim_material.material_id.unique|uniqueness|High|raw|True|{}|
|dim_material.material_id.pattern|validity|High|cleaned|True|{"pattern": "M[0-9]{5}"}|
|dim_material.material_id.reference|referential_integrity|Critical|cleaned|True|{"reference": true, "target": "dim_material"}|
|dim_material.supplier_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_supplier"}|
|dim_material.uom.allowed|validity|Medium|cleaned|True|{"values": ["EA", "KG", "L"]}|
|dim_material.uom.canonical_unit|consistency|Medium|raw|False|{}|
|dim_material.material_name.canonical_label|consistency|Medium|raw|False|{"key": "material_id"}|
|dim_warehouse.warehouse_id.not_null|completeness|High|cleaned|True|{}|
|dim_warehouse.facility_id.not_null|completeness|High|cleaned|True|{}|
|dim_warehouse.warehouse_name.not_null|completeness|High|cleaned|True|{}|
|dim_warehouse.warehouse_id.unique|uniqueness|High|raw|True|{}|
|dim_warehouse.warehouse_id.pattern|validity|High|cleaned|True|{"pattern": "W[0-9]{3}"}|
|dim_warehouse.warehouse_id.reference|referential_integrity|Critical|cleaned|True|{"reference": true, "target": "dim_warehouse"}|
|dim_warehouse.facility_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_facility"}|
|dim_warehouse.warehouse_name.canonical_label|consistency|Medium|raw|False|{"key": "warehouse_id"}|
|fact_sales_order.order_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.customer_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.product_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.facility_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.order_date.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.quantity.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.unit_price.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.uom.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order.order_id.unique|uniqueness|High|raw|True|{}|
|fact_sales_order.order_id.pattern|validity|High|cleaned|True|{"pattern": "O[0-9]{5}"}|
|fact_sales_order.customer_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_customer"}|
|fact_sales_order.product_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_product"}|
|fact_sales_order.facility_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_facility"}|
|fact_sales_order.quantity.nonnegative|validity|High|cleaned|True|{}|
|fact_sales_order.unit_price.nonnegative|validity|High|cleaned|True|{}|
|fact_sales_order.quantity.upper_bound|anomaly|Medium|cleaned|False|{"maximum": 5000}|
|fact_sales_order.uom.allowed|validity|Medium|cleaned|True|{"values": ["EA", "KG", "L"]}|
|fact_sales_order.uom.canonical_unit|consistency|Medium|raw|False|{}|
|fact_sales_order.uom.product_unit|consistency|High|cleaned|True|{}|
|fact_sales_order.order_date.date|validity|High|cleaned|True|{}|
|fact_sales_order.order_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_sales_order_line.line_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.order_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.product_id.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.order_date.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.quantity.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.unit_price.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.uom.not_null|completeness|High|cleaned|True|{}|
|fact_sales_order_line.line_id.unique|uniqueness|High|raw|True|{}|
|fact_sales_order_line.line_id.pattern|validity|High|cleaned|True|{"pattern": "OL[0-9]{5}"}|
|fact_sales_order_line.order_id.reference|referential_integrity|Critical|cleaned|True|{"target": "fact_sales_order"}|
|fact_sales_order_line.product_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_product"}|
|fact_sales_order_line.quantity.nonnegative|validity|High|cleaned|True|{}|
|fact_sales_order_line.unit_price.nonnegative|validity|High|cleaned|True|{}|
|fact_sales_order_line.quantity.upper_bound|anomaly|Medium|cleaned|False|{"maximum": 5000}|
|fact_sales_order_line.uom.allowed|validity|Medium|cleaned|True|{"values": ["EA", "KG", "L"]}|
|fact_sales_order_line.uom.canonical_unit|consistency|Medium|raw|False|{}|
|fact_sales_order_line.uom.product_unit|consistency|High|cleaned|True|{}|
|fact_sales_order_line.order_date.date|validity|High|cleaned|True|{}|
|fact_sales_order_line.order_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_sales_order_line.order_id.order_line|consistency|High|cleaned|True|{}|
|fact_production.production_id.not_null|completeness|High|cleaned|True|{}|
|fact_production.product_id.not_null|completeness|High|cleaned|True|{}|
|fact_production.facility_id.not_null|completeness|High|cleaned|True|{}|
|fact_production.material_id.not_null|completeness|High|cleaned|True|{}|
|fact_production.production_date.not_null|completeness|High|cleaned|True|{}|
|fact_production.quantity.not_null|completeness|High|cleaned|True|{}|
|fact_production.uom.not_null|completeness|High|cleaned|True|{}|
|fact_production.production_id.unique|uniqueness|High|raw|True|{}|
|fact_production.production_id.pattern|validity|High|cleaned|True|{"pattern": "PR[0-9]{5}"}|
|fact_production.product_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_product"}|
|fact_production.facility_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_facility"}|
|fact_production.material_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_material"}|
|fact_production.quantity.nonnegative|validity|High|cleaned|True|{}|
|fact_production.quantity.upper_bound|anomaly|Medium|cleaned|False|{"maximum": 8000}|
|fact_production.uom.allowed|validity|Medium|cleaned|True|{"values": ["EA", "KG", "L"]}|
|fact_production.uom.canonical_unit|consistency|Medium|raw|False|{}|
|fact_production.uom.product_unit|consistency|High|cleaned|True|{}|
|fact_production.production_date.date|validity|High|cleaned|True|{}|
|fact_production.production_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_inventory.inventory_id.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.product_id.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.facility_id.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.warehouse_id.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.stock_date.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.quantity.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.uom.not_null|completeness|High|cleaned|True|{}|
|fact_inventory.inventory_id.unique|uniqueness|High|raw|True|{}|
|fact_inventory.inventory_id.pattern|validity|High|cleaned|True|{"pattern": "I[0-9]{5}"}|
|fact_inventory.product_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_product"}|
|fact_inventory.facility_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_facility"}|
|fact_inventory.warehouse_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_warehouse"}|
|fact_inventory.quantity.nonnegative|validity|High|cleaned|True|{}|
|fact_inventory.quantity.upper_bound|anomaly|Medium|cleaned|False|{"maximum": 10000}|
|fact_inventory.uom.allowed|validity|Medium|cleaned|True|{"values": ["EA", "KG", "L"]}|
|fact_inventory.uom.canonical_unit|consistency|Medium|raw|False|{}|
|fact_inventory.uom.product_unit|consistency|High|cleaned|True|{}|
|fact_inventory.stock_date.date|validity|High|cleaned|True|{}|
|fact_inventory.stock_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_inventory.warehouse_id.warehouse_facility|consistency|High|cleaned|True|{}|
|fact_shipment.shipment_id.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.order_id.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.facility_id.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.carrier.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.ship_date.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.promised_date.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.delivery_date.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.quantity.not_null|completeness|High|cleaned|True|{}|
|fact_shipment.shipment_id.unique|uniqueness|High|raw|True|{}|
|fact_shipment.shipment_id.pattern|validity|High|cleaned|True|{"pattern": "SH[0-9]{5}"}|
|fact_shipment.order_id.reference|referential_integrity|Critical|cleaned|True|{"target": "fact_sales_order"}|
|fact_shipment.facility_id.reference|referential_integrity|Critical|cleaned|True|{"target": "dim_facility"}|
|fact_shipment.quantity.nonnegative|validity|High|cleaned|True|{}|
|fact_shipment.quantity.upper_bound|anomaly|Medium|cleaned|False|{"maximum": 5000}|
|fact_shipment.ship_date.date|validity|High|cleaned|True|{}|
|fact_shipment.ship_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_shipment.promised_date.date|validity|High|cleaned|True|{}|
|fact_shipment.promised_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_shipment.delivery_date.date|validity|High|cleaned|True|{}|
|fact_shipment.delivery_date.not_future|timeliness|Medium|cleaned|True|{}|
|fact_shipment.delivery_date.date_order|validity|High|cleaned|True|{"earlier": "ship_date"}|
|fact_shipment.promised_date.date_order|validity|High|cleaned|True|{"earlier": "ship_date"}|
|fact_shipment.ship_date.shipment_order|consistency|High|cleaned|True|{}|
|fact_shipment.delivery_date.delivery_delay|anomaly|Low|cleaned|False|{"maximum": 90}|
