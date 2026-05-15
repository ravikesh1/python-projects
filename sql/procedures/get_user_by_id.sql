-- get_user_by_id(p_id) -> single user row
DROP PROCEDURE IF EXISTS get_user_by_id;

DELIMITER $$

CREATE PROCEDURE get_user_by_id(IN p_id BIGINT UNSIGNED)
BEGIN
  SELECT id, email, display_name, is_active, created_at, updated_at
  FROM users
  WHERE id = p_id;
END$$

DELIMITER ;
