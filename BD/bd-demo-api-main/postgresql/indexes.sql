CREATE INDEX idx_leilao_fim ON leilao (fim);
CREATE INDEX idx_leilao_descricao_artigo ON leilao (descricao, artigo_ean);
CREATE INDEX idx_leilao_username ON leilao (utilizador_username);
CREATE INDEX idx_memsagem_leilao_utilizador ON mensagem (leilao_id, utilizador_username);
CREATE INDEX idx_licitacao_leilao_utilizador ON licitacao (leilao_id, utilizador_username);
CREATE INDEX idx_versao_leilao ON versao (leilao_id);
