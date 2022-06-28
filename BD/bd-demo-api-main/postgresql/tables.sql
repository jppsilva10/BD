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
