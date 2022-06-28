CREATE OR REPLACE FUNCTION notify_mensagem() returns trigger
language plpgsql
AS $$
BEGIN 
	INSERT INTO mensagem_notificacao (utilizador_username, mensagem_id)
	SELECT ut.username, NEW.id
		FROM utilizador ut
		WHERE ut.username <> NEW.utilizador_username AND
		(EXISTS (SELECT FROM leilao le WHERE le.id = NEW.leilao_id AND le.utilizador_username = ut.username) OR
		EXISTS (SELECT FROM mensagem me WHERE me.leilao_id = NEW.leilao_id AND me.utilizador_username = ut.username));
	
	-- idx_leilao_utilizador_id
	-- idx_memsagem_leilao_utilizador

	RETURN NEW;
END
$$;

CREATE TRIGGER after_mensagem
AFTER INSERT
ON mensagem
FOR EACH ROW
EXECUTE PROCEDURE notify_mensagem();
