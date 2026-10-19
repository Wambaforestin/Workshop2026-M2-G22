-- Jeu de données fictif de démarrage (SI de paiement simulé).
-- Chargé automatiquement par l'image Postgres au premier démarrage.

CREATE TABLE IF NOT EXISTS accounts (
    id       TEXT PRIMARY KEY,
    owner    TEXT NOT NULL,
    balance  NUMERIC(14,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    destination TEXT NOT NULL,
    amount      NUMERIC(14,2) NOT NULL,
    status      TEXT NOT NULL,
    created_by  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO accounts (id, owner, balance) VALUES
  ('acc-merchant-001', 'Boutique Fictive SAS', 100000.00),
  ('acc-client-001',   'Client Démo A',         5000.00),
  ('acc-client-002',   'Client Démo B',         5000.00)
ON CONFLICT (id) DO NOTHING;
