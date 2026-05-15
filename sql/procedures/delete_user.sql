-- delete_user(p_id) -> { deleted_rows }
DROP PROCEDURE IF EXISTS delete_user;

DELIMITER $$

CREATE PROCEDURE delete_user(IN p_id BIGINT UNSIGNED)
BEGIN
  DELETE FROM users WHERE id = p_id;
  SELECT ROW_COUNT() AS deleted_rows;
END$$

DELIMITER ;
