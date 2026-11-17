-- name: customers_missing_email | table: customers
SELECT COUNT(*) FROM customers WHERE email IS NULL OR email = '';

-- name: customers_duplicate_email | table: customers
SELECT COUNT(*) FROM (
    SELECT email FROM customers
    WHERE email IS NOT NULL
    GROUP BY email
    HAVING COUNT(*) > 1
);

-- name: products_invalid_price | table: products
SELECT COUNT(*) FROM products WHERE price IS NULL OR price <= 0;

-- name: order_items_negative_quantity | table: order_items
SELECT COUNT(*) FROM order_items WHERE quantity IS NULL OR quantity <= 0;

-- name: orders_orphan_customer | table: orders
SELECT COUNT(*) FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- name: order_items_orphan_order | table: order_items
SELECT COUNT(*) FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

-- name: order_items_orphan_product | table: order_items
SELECT COUNT(*) FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

-- name: orders_future_date | table: orders
SELECT COUNT(*) FROM orders WHERE order_date > datetime('now');

-- name: orders_invalid_status | table: orders
SELECT COUNT(*) FROM orders
WHERE status NOT IN ('pending', 'shipped', 'delivered', 'cancelled');