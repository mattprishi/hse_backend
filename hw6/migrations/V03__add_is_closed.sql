-- Add is_closed column to ads table
ALTER TABLE ads ADD COLUMN is_closed BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_ads_is_closed ON ads(is_closed);
