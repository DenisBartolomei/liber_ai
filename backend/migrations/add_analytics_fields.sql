-- ===========================================
-- Add analytics fields to existing tables
-- ===========================================

-- Add budget_initial and num_bottiglie_target to sessions table
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS budget_initial NUMERIC(10, 2);

ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS num_bottiglie_target INTEGER;

-- Add margin to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS margin NUMERIC(10, 2);

-- Create function to calculate margin
CREATE OR REPLACE FUNCTION calculate_product_margin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price IS NOT NULL AND NEW.cost_price IS NOT NULL THEN
        NEW.margin = GREATEST(0, NEW.price - NEW.cost_price);
    ELSE
        NEW.margin = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-calculate margin when price or cost_price changes
DROP TRIGGER IF EXISTS trigger_calculate_product_margin ON products;
CREATE TRIGGER trigger_calculate_product_margin
    BEFORE INSERT OR UPDATE OF price, cost_price ON products
    FOR EACH ROW
    EXECUTE FUNCTION calculate_product_margin();

-- Update existing products to calculate margin
UPDATE products 
SET margin = GREATEST(0, price - cost_price)
WHERE price IS NOT NULL AND cost_price IS NOT NULL;

