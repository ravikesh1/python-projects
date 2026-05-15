-- list_users(p_limit, p_offset) -> paginated user rows ordered by id
DROP PROCEDURE IF EXISTS list_users;

DELIMITER $$

CREATE PROCEDURE list_users(IN p_limit INT, IN p_offset INT)
BEGIN
  IF p_limit IS NULL OR p_limit <= 0 THEN
    SET p_limit = 100;
  END IF;
  IF p_offset IS NULL OR p_offset < 0 THEN
    SET p_offset = 0;
  END IF;

  SELECT id, email, display_name, is_active, created_at, updated_at
  FROM users
  ORDER BY id
  LIMIT p_limit OFFSET p_offset;
END$$

DELIMITER ;
