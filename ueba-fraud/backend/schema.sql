CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  country TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  suspicious_activity BOOLEAN DEFAULT FALSE,
  profile JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  ts TIMESTAMPTZ NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  type TEXT CHECK (type IN ('payment','withdrawal','deposit','transfer')),
  country TEXT,
  device_fingerprint TEXT,
  ip TEXT,
  is_fraud BOOLEAN,
  anomaly_score DOUBLE PRECISION,
  rules_score DOUBLE PRECISION,
  final_risk DOUBLE PRECISION,
  anomaly_flag SMALLINT,
  explanations JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS actions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  txn_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
  action TEXT CHECK (action IN ('LOCK_ACCOUNT','STEP_UP','FALSE_POSITIVE')) NOT NULL,
  note TEXT,
  actor TEXT DEFAULT 'analyst',
  ts TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_thresholds (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  base_threshold DOUBLE PRECISION DEFAULT 0.75,
  bias DOUBLE PRECISION DEFAULT 0.0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tx_user_ts ON transactions(user_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_tx_risk    ON transactions(final_risk DESC);
CREATE INDEX IF NOT EXISTS idx_tx_anom    ON transactions(anomaly_flag);
-- Extra indexes for new rules
CREATE INDEX IF NOT EXISTS idx_tx_device_ts ON transactions(device_fingerprint, ts DESC);
CREATE INDEX IF NOT EXISTS idx_tx_user_type_ts ON transactions(user_id, type, ts DESC);
