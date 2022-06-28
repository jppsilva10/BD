CREATE OR REPLACE FUNCTION close_leilao(le_id leilao.id%type) RETURNS licitacao.utilizador_username%type
language plpgsql
AS $$
DECLARE
	c1 CURSOR FOR
	SELECT MAX(valor), utilizador_username
	from licitacao
	where leilao_id = le_id
	GROUP BY utilizador_username;

	bid licitacao.valor%type;
	vencedor licitacao.utilizador_username%type;
BEGIN 
	
	IF NOT EXISTS(SELECT FROM leilao WHERE id = le_id) THEN
		raise exception 'Auction not found';
	END IF;

	Update leilao SET terminado = TRUE
	WHERE leilao.id = le_id AND NOT leilao.terminado;

	OPEN c1;
	FETCH c1 INTO bid, vencedor;
	CLOSE c1;
	RETURN vencedor;
END
$$;


CREATE OR REPLACE FUNCTION edit_leilao() returns trigger
language plpgsql
AS $$
BEGIN 
	-- se foi editado
	IF NOT ( NOT OLD.terminado AND NEW.terminado ) THEN
		INSERT INTO versao (titulo, descricao, leilao_id)
        	Values (OLD.titulo, OLD.descricao, OLD.id);
	END IF;

	RETURN NEW;
END
$$;

CREATE TRIGGER after_edit
AFTER UPDATE
ON leilao
FOR EACH ROW
EXECUTE PROCEDURE edit_leilao();

CREATE OR REPLACE FUNCTION dont_close() returns trigger
language plpgsql
AS $$
BEGIN 
	IF ( NOT OLD.terminado AND NEW.terminado ) AND ( OLD.fim > CURRENT_TIMESTAMP + '01:00' ) THEN
		raise exception 'You must wait until %s to close the auction', OLD.fim;
	END IF;

	RETURN NEW;
END
$$;

CREATE TRIGGER before_close
AFTER UPDATE
ON leilao
FOR EACH ROW
EXECUTE PROCEDURE dont_close();

CREATE OR REPLACE FUNCTION validate_fim() returns trigger
language plpgsql
AS $$
BEGIN 
	IF NEW.fim < CURRENT_TIMESTAMP + '01:00' THEN
		raise exception 'Fim has to be after %s', CURRENT_TIMESTAMP + '01:00';
	END IF;

	RETURN NEW;
END
$$;

CREATE TRIGGER check_fim
BEFORE INSERT
ON leilao
FOR EACH ROW
EXECUTE PROCEDURE validate_fim();