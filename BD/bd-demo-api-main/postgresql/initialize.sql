CREATE TABLE utilizador (
	username VARCHAR(256),
	email	 VARCHAR(256) UNIQUE NOT NULL,
	password VARCHAR(256) NOT NULL,
	authtoken VARCHAR(32) UNIQUE NOT NULL,
	PRIMARY KEY(username)
);

CREATE TABLE leilao (
	id BIGSERIAL,
	titulo VARCHAR(128) NOT NULL,
	descricao VARCHAR(512) NOT NULL,
	preco INTEGER NOT NULL DEFAULT 0,
	fim TIMESTAMP NOT NULL,
	terminado BOOL NOT NULL DEFAULT FALSE,
	artigo_ean VARCHAR(13) NOT NULL,
	utilizador_username VARCHAR(256) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE artigo (
	ean VARCHAR(13),
	PRIMARY KEY(ean)
);

CREATE TABLE mensagem (
	id BIGSERIAL,
	conteudo VARCHAR(512) NOT NULL,
	instante TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP + '01:00',
	leilao_id BIGSERIAL NOT NULL,
	utilizador_username VARCHAR(256) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE licitacao (
	valor INTEGER,
	instante TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP + '01:00',
	leilao_id BIGSERIAL,
	utilizador_username VARCHAR(256) NOT NULL,
	PRIMARY KEY(valor,leilao_id)
);

CREATE TABLE versao (
	id SMALLSERIAL,
	titulo VARCHAR(128) NOT NULL,
	descricao VARCHAR(512) NOT NULL,
	instante TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP + '01:00',
	leilao_id BIGSERIAL,
	PRIMARY KEY(leilao_id, id)
);

CREATE TABLE licitacao_notificacao (
	licitacao_valor INTEGER,
	licitacao_leilao_id BIGSERIAL,
	licitacao_ultrapassada_valor INTEGER NOT NULL,
	licitacao_ultrapassada_leilao_id BIGSERIAL NOT NULL,
	PRIMARY KEY(licitacao_valor, licitacao_leilao_id)
);

CREATE TABLE mensagem_notificacao (
	utilizador_username VARCHAR(256),
	mensagem_id BIGSERIAL,
	PRIMARY KEY(utilizador_username,mensagem_id)
);

ALTER TABLE utilizador ADD CONSTRAINT constraint_email CHECK (email LIKE '%@%');
ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (artigo_ean) REFERENCES artigo(ean);
ALTER TABLE leilao ADD CONSTRAINT leilao_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE leilao ADD CONSTRAINT constraint_preco CHECK (preco>=0);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT constraint_valor CHECK (valor>0);
ALTER TABLE versao ADD CONSTRAINT versao_fk1 FOREIGN KEY (leilao_id) REFERENCES leilao(id);
ALTER TABLE licitacao_notificacao ADD CONSTRAINT licitacao_notificacao_fk1 FOREIGN KEY (licitacao_valor, licitacao_leilao_id) REFERENCES licitacao(valor, leilao_id);
ALTER TABLE licitacao_notificacao ADD CONSTRAINT licitacao_notificacao_fk2 FOREIGN KEY (licitacao_ultrapassada_valor, licitacao_ultrapassada_leilao_id) REFERENCES licitacao(valor, leilao_id);
ALTER TABLE licitacao_notificacao ADD CONSTRAINT licitacao_ultrapassada_unique UNIQUE (licitacao_ultrapassada_valor, licitacao_ultrapassada_leilao_id);
ALTER TABLE mensagem_notificacao ADD CONSTRAINT mensagem_notificacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem_notificacao ADD CONSTRAINT mensagem_notificacao_fk2 FOREIGN KEY (mensagem_id) REFERENCES mensagem(id);

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

CREATE OR REPLACE FUNCTION get_username(auth utilizador.authtoken%type) RETURNS utilizador.username%type
language plpgsql
AS $$
BEGIN 
	RETURN( SELECT username FROM utilizador WHERE authtoken = auth );
	-- utilizador_authtoken_key index
END
$$;

CREATE OR REPLACE FUNCTION validate(auth utilizador.authtoken%type) RETURNS utilizador.username%type
language plpgsql
AS $$
DECLARE
	value utilizador.username%type;
BEGIN 
	value = get_username(auth);
	
	IF value IS NULL THEN
		raise exception 'Invalid authToken' USING ERRCODE = '18456';
	END IF;

	RETURN value;
END
$$;

CREATE INDEX idx_leilao_fim ON leilao (fim);
CREATE INDEX idx_leilao_descricao_artigo ON leilao (descricao, artigo_ean);
CREATE INDEX idx_leilao_username ON leilao (utilizador_username);
CREATE INDEX idx_memsagem_leilao_utilizador ON mensagem (leilao_id, utilizador_username);
CREATE INDEX idx_licitacao_leilao_utilizador ON licitacao (leilao_id, utilizador_username);
CREATE INDEX idx_versao_leilao ON versao (leilao_id);
