-- upsert_user(p_email, p_display_name, p_is_active) -> selects the resulting user row.
-- Inserts a new user keyed on email, or updates display_name / is_active if the
-- email already exists. Returns the row so callers see the final state.
DROP PROCEDURE IF EXISTS upsert_user;

DELIMITER $$

CREATE PROCEDURE upsert_user(
  IN p_email        VARCHAR(255),
  IN p_display_name VARCHAR(255),
  IN p_is_active    TINYINT
)
BEGIN
  INSERT INTO users (email, display_name, is_active)
  VALUES (p_email, p_display_name, COALESCE(p_is_active, 1))
  ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    is_active    = VALUES(is_active);

  SELECT id, email, display_name, is_active, created_at, updated_at
  FROM users
  WHERE email = p_email;
END$$

DELIMITER ;
