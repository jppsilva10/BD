CREATE OR REPLACE FUNCTION insert_licitacao() returns trigger
language plpgsql
AS $$
BEGIN 
	-- se lelao ja acabou
	IF EXISTS (SELECT FROM leilao le WHERE le.id = NEW.leilao_id AND le.fim <= NEW.instante) THEN
		-- anula a insercao
		-- RETURN NULL;
		raise exception 'The auction is already closed';

	-- se houver uma licitacao for menor que o preco minimo
	ELSIF EXISTS (SELECT FROM leilao le WHERE le.id = NEW.leilao_id AND le.preco > NEW.valor) THEN
		-- anula a insercao
		-- RETURN NULL;
		raise exception 'The bid cant be lower than the starting price';

	-- se houver uma licitacao com valor maior ou igual	
	ELSIF EXISTS (SELECT FROM licitacao li WHERE li.leilao_id = NEW.leilao_id AND li.valor >= NEW.valor) THEN
		-- anula a insercao
		-- RETURN NULL;
		raise exception 'The bid must be higher than the previous one';
	ELSE
		-- valida a insercao
		RETURN NEW;
	END IF;

	-- idx_licitacao_fim_id
	-- idx_licitacao_leilao_utilizador
	-- leilao_pkey index
END
$$;

CREATE TRIGGER before_licitacao
BEFORE INSERT
ON licitacao
FOR EACH ROW
EXECUTE PROCEDURE insert_licitacao();

CREATE OR REPLACE FUNCTION notify_licitacao() returns trigger
language plpgsql
AS $$
BEGIN 
	INSERT INTO licitacao_notificacao (licitacao_valor, licitacao_leilao_id, licitacao_ultrapassada_valor, licitacao_ultrapassada_leilao_id)
	SELECT NEW.valor, NEW.leilao_id, MAX(li.valor), li.leilao_id
		FROM licitacao li
		WHERE li.leilao_id = NEW.leilao_id AND li.valor <> NEW.valor AND li.utilizador_username <> NEW.utilizador_username
		GROUP BY li.leilao_id;

		-- idx_licitacao_leilao_utilizador

	RETURN NEW;
END
$$;

CREATE TRIGGER after_licitacao
AFTER INSERT
ON licitacao
FOR EACH ROW
EXECUTE PROCEDURE notify_licitacao();
