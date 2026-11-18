# Data dictionary

Generated from the actual field contracts. See DATA_MODEL.md for table grains.

|Table|Field|Type|Meaning|Critical|Owner|
|---|---|---|---|---|---|
|dim_customer|customer_id|string|Unique identifier for customer; resolves to master or transaction parent.|True|ERP Business Owner|
|dim_customer|customer_name|string|Canonical customer name in the fictional PackRight dataset.|False|ERP Business Owner|
|dim_customer|country|string|Canonical country in the fictional PackRight dataset.|False|ERP Business Owner|
|dim_product|product_id|string|Unique identifier for product; resolves to master or transaction parent.|True|ERP Business Owner|
|dim_product|product_description|string|Canonical product description in the fictional PackRight dataset.|False|ERP Business Owner|
|dim_product|category|string|Packaging family from the controlled product-category reference.|True|ERP Business Owner|
|dim_product|uom|string|Standard unit: EA=each, KG=kilogram, L=litre.|False|ERP Business Owner|
|dim_product|supplier_id|string|Unique identifier for supplier; resolves to master or transaction parent.|True|ERP Business Owner|
|dim_facility|facility_id|string|Unique identifier for facility; resolves to master or transaction parent.|True|MASTER_DATA Business Owner|
|dim_facility|facility_name|string|Canonical facility name in the fictional PackRight dataset.|False|MASTER_DATA Business Owner|
|dim_facility|city|string|Canonical city in the fictional PackRight dataset.|False|MASTER_DATA Business Owner|
|dim_supplier|supplier_id|string|Unique identifier for supplier; resolves to master or transaction parent.|True|MASTER_DATA Business Owner|
|dim_supplier|supplier_name|string|Canonical supplier name in the fictional PackRight dataset.|False|MASTER_DATA Business Owner|
|dim_supplier|country|string|Canonical country in the fictional PackRight dataset.|False|MASTER_DATA Business Owner|
|dim_material|material_id|string|Unique identifier for material; resolves to master or transaction parent.|True|MASTER_DATA Business Owner|
|dim_material|material_name|string|Canonical material name in the fictional PackRight dataset.|False|MASTER_DATA Business Owner|
|dim_material|supplier_id|string|Unique identifier for supplier; resolves to master or transaction parent.|True|MASTER_DATA Business Owner|
|dim_material|uom|string|Standard unit: EA=each, KG=kilogram, L=litre.|False|MASTER_DATA Business Owner|
|dim_warehouse|warehouse_id|string|Unique identifier for warehouse; resolves to master or transaction parent.|True|WMS Business Owner|
|dim_warehouse|facility_id|string|Unique identifier for facility; resolves to master or transaction parent.|True|WMS Business Owner|
|dim_warehouse|warehouse_name|string|Canonical warehouse name in the fictional PackRight dataset.|False|WMS Business Owner|
|fact_sales_order|order_id|string|Unique identifier for order; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order|customer_id|string|Unique identifier for customer; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order|product_id|string|Unique identifier for product; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order|facility_id|string|Unique identifier for facility; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order|order_date|date|Calendar day when the fictional order was placed.|True|ERP Business Owner|
|fact_sales_order|quantity|decimal|Number of units at this table's documented grain; interpret with uom.|True|ERP Business Owner|
|fact_sales_order|unit_price|decimal|Synthetic INR price per ordered unit; sales value is quantity times unit price.|False|ERP Business Owner|
|fact_sales_order|uom|string|Standard unit: EA=each, KG=kilogram, L=litre.|False|ERP Business Owner|
|fact_sales_order_line|line_id|string|Unique identifier for line; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order_line|order_id|string|Unique identifier for order; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order_line|product_id|string|Unique identifier for product; resolves to master or transaction parent.|True|ERP Business Owner|
|fact_sales_order_line|order_date|date|Calendar day when the fictional order was placed.|True|ERP Business Owner|
|fact_sales_order_line|quantity|decimal|Number of units at this table's documented grain; interpret with uom.|True|ERP Business Owner|
|fact_sales_order_line|unit_price|decimal|Synthetic INR price per ordered unit; sales value is quantity times unit price.|False|ERP Business Owner|
|fact_sales_order_line|uom|string|Standard unit: EA=each, KG=kilogram, L=litre.|False|ERP Business Owner|
|fact_production|production_id|string|Unique identifier for production; resolves to master or transaction parent.|True|MES Business Owner|
|fact_production|product_id|string|Unique identifier for product; resolves to master or transaction parent.|True|MES Business Owner|
|fact_production|facility_id|string|Unique identifier for facility; resolves to master or transaction parent.|True|MES Business Owner|
|fact_production|material_id|string|Unique identifier for material; resolves to master or transaction parent.|True|MES Business Owner|
|fact_production|production_date|date|Calendar day of completed synthetic production.|True|MES Business Owner|
|fact_production|quantity|decimal|Number of units at this table's documented grain; interpret with uom.|True|MES Business Owner|
|fact_production|uom|string|Standard unit: EA=each, KG=kilogram, L=litre.|False|MES Business Owner|
|fact_inventory|inventory_id|string|Unique identifier for inventory; resolves to master or transaction parent.|True|WMS Business Owner|
|fact_inventory|product_id|string|Unique identifier for product; resolves to master or transaction parent.|True|WMS Business Owner|
|fact_inventory|facility_id|string|Unique identifier for facility; resolves to master or transaction parent.|True|WMS Business Owner|
|fact_inventory|warehouse_id|string|Unique identifier for warehouse; resolves to master or transaction parent.|True|WMS Business Owner|
|fact_inventory|stock_date|date|Inventory observation day; never sum balances across observation dates.|True|WMS Business Owner|
|fact_inventory|quantity|decimal|Number of units at this table's documented grain; interpret with uom.|True|WMS Business Owner|
|fact_inventory|uom|string|Standard unit: EA=each, KG=kilogram, L=litre.|False|WMS Business Owner|
|fact_shipment|shipment_id|string|Unique identifier for shipment; resolves to master or transaction parent.|True|LOGISTICS Business Owner|
|fact_shipment|order_id|string|Unique identifier for order; resolves to master or transaction parent.|True|LOGISTICS Business Owner|
|fact_shipment|facility_id|string|Unique identifier for facility; resolves to master or transaction parent.|True|LOGISTICS Business Owner|
|fact_shipment|carrier|string|Canonical carrier in the fictional PackRight dataset.|False|LOGISTICS Business Owner|
|fact_shipment|ship_date|date|Day goods left the facility.|True|LOGISTICS Business Owner|
|fact_shipment|promised_date|date|Promised delivery deadline.|True|LOGISTICS Business Owner|
|fact_shipment|delivery_date|date|Actual synthetic delivery day.|True|LOGISTICS Business Owner|
|fact_shipment|quantity|decimal|Number of units at this table's documented grain; interpret with uom.|True|LOGISTICS Business Owner|
