CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  unique_id TEXT,
  zip_code_prefix TEXT,
  city TEXT,
  state TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
  id TEXT PRIMARY KEY,
  category TEXT,
  name_length INTEGER,
  description_length INTEGER,
  photos_qty INTEGER,
  weight_g INTEGER,
  length_cm INTEGER,
  height_cm INTEGER,
  width_cm INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  status TEXT,
  purchase_at TIMESTAMPTZ,
  approved_at TIMESTAMPTZ,
  delivered_carrier_at TIMESTAMPTZ,
  delivered_customer_at TIMESTAMPTZ,
  estimated_delivery_at TIMESTAMPTZ,
  total_amount NUMERIC(14, 2) DEFAULT 0,
  created_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS order_items (
  id BIGSERIAL PRIMARY KEY,
  order_id TEXT REFERENCES orders(id),
  item_seq INTEGER,
  product_id TEXT REFERENCES products(id),
  seller_id TEXT,
  shipping_limit_at TIMESTAMPTZ,
  price NUMERIC(14, 2),
  freight_value NUMERIC(14, 2)
);

CREATE TABLE IF NOT EXISTS payments (
  id BIGSERIAL PRIMARY KEY,
  order_id TEXT REFERENCES orders(id),
  payment_sequential INTEGER,
  payment_type TEXT,
  installments INTEGER,
  amount NUMERIC(14, 2),
  status TEXT DEFAULT 'paid',
  paid_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS refunds (
  id BIGSERIAL PRIMARY KEY,
  order_id TEXT REFERENCES orders(id),
  amount NUMERIC(14, 2),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reviews (
  id TEXT PRIMARY KEY,
  order_id TEXT REFERENCES orders(id),
  score INTEGER,
  comment_title TEXT,
  comment_message TEXT,
  created_at TIMESTAMPTZ,
  answered_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS traffic_events (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  event_type TEXT NOT NULL,
  source TEXT,
  product_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS coupons (
  id BIGSERIAL PRIMARY KEY,
  code TEXT NOT NULL,
  discount_type TEXT NOT NULL,
  discount_value NUMERIC(14, 2) NOT NULL,
  starts_at TIMESTAMPTZ,
  ends_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS coupon_usages (
  id BIGSERIAL PRIMARY KEY,
  coupon_id BIGINT REFERENCES coupons(id),
  user_id TEXT REFERENCES users(id),
  order_id TEXT REFERENCES orders(id),
  used_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS inventory_snapshots (
  id BIGSERIAL PRIMARY KEY,
  product_id TEXT REFERENCES products(id),
  stock_qty INTEGER NOT NULL,
  snapshot_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_costs (
  product_id TEXT PRIMARY KEY REFERENCES products(id),
  unit_cost NUMERIC(14, 2) NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments (order_id);
CREATE INDEX IF NOT EXISTS idx_refunds_order_id ON refunds (order_id);
