
from flask import Flask, jsonify, request
import logging, psycopg2, time

import hashlib
import random

def encrypt(string):
    return hashlib.md5( string.encode() ).hexdigest()

##########################################################
## ENDPOINTS
##########################################################

app = Flask(__name__) 

@app.route('/') 
def hello(): 
    return """

    Hello World!  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/>
    BD 2021 Team<br/>
    <br/>
    """

##
##  Registo	de artigos
##  http://localhost:8080/dbproj/artigo
##

@app.route("/dbproj/artigo", methods=['POST'])
def create_product():
    logger.info("###              DEMO: POST /dbproj/artigo             ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new product  ----")
    logger.debug(f'payload: {payload}')

    if "ean" not in payload:
        if conn is not None:
            conn.close()
        return 'ean code is required to create a product'

    statement = """
                INSERT INTO artigo (ean)
                VALUES ( %s )
                RETURNING ean"""

    # utilizador_pkey

    try:
        cur.execute(statement, (payload["ean"], ))
        ean = cur.fetchone()[0]
        result = {'artigoId': ean}
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##
##  Registo	de	utilizadores
##  http://localhost:8080/dbproj/user
##

@app.route("/dbproj/user", methods=['POST'])
def create_account():
    logger.info("###              DEMO: POST /dbproj/user             ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new user  ----")
    logger.debug(f'payload: {payload}')

    if "username" not in payload or "email" not in payload or "password" not in payload:
        if conn is not None:
            conn.close()
        return 'username, email and password are required to create an account'

    statement = """
                INSERT INTO utilizador (username, email, password, authtoken)
                VALUES ( %s,   %s ,   %s ,   %s )
                RETURNING username"""

    # utilizador_pkey

    authToken = encrypt( payload["username"] + str(random.randint(0, 100000)) )
    values = (payload["username"], payload["email"], encrypt(payload["password"]), authToken, )

    try:
        cur.execute(statement, values)
        username = cur.fetchone()[0]
        result = {'UserId': username}
        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##
##  Autenticacao de	utilizadores
##  http://localhost:8080/dbproj/user
##

@app.route("/dbproj/user", methods=['PUT'])
def user_authentication():
    logger.info("###              DEMO: PUT /dbproj/user              ###");   
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    if "username" not in content or "password" not in content:
        if conn is not None:
            conn.close()
        return 'username and password are required for user authentication'


    logger.info("---- user authentication  ----")
    logger.info(f'content: {content}')

    statement ="""
                UPDATE utilizador 
                  SET authtoken = %s
                WHERE username = %s and password = %s
                RETURNING authtoken"""

    # utilizador_authtoken_key

    authToken = encrypt( content["username"] + str(random.randint(0, 100000)) )
    values = (authToken, content["username"], encrypt(content["password"]), )

    try:
        cur.execute(statement, values)

        if int(cur.rowcount) == 0:
            result = {'erro': 'AuthError'}
        else:
            authToken = cur.fetchone()[0]
            result = {'authToken': authToken}

        cur.execute("commit")
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)

##
##  Criar um novo leilao
##  http://localhost:8080/dbproj/leilao
##

@app.route("/dbproj/leilao", methods=['POST'])
def create_auction():
    logger.info("###              DEMO: POST /dbproj/leilao            ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new auction  ----")
    logger.debug(f'payload: {payload}')

    if "authToken" not in payload:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    if "artigoId" not in payload or "precoMinimo" not in payload or "titulo" not in payload or "descricao" not in payload or "fim" not in payload:
        if conn is not None:
            conn.close()
        return 'artigoId, precoMinimo, titulo, descricao and fim are required to create an auction'

    statement = """
                INSERT INTO leilao (titulo, descricao, preco, fim, artigo_ean, utilizador_username)
                SELECT %s,   %s ,   %s,   %s ,   %s, username
                    FROM utilizador
                    WHERE authtoken = %s
                RETURNING id"""

    # utilizador_authtoken_key

    values = (payload["titulo"], payload["descricao"], payload["precoMinimo"], payload["fim"], payload["artigoId"], payload["authToken"], )

    try:
        cur.execute(statement, values)
        if int(cur.rowcount) == 0:
            cur.execute("rollback")
            if conn is not None:
                conn.close()
            return jsonify({'erro': 'AuthError'})

        leilaoId = cur.fetchone()[0]
        cur.execute("commit")
        result = {'leilaoId': leilaoId}
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##
##  Listar todos os leiloes existentes
##  http://localhost:8080/dbproj/leiloes
##

@app.route("/dbproj/leiloes", methods=['GET'], strict_slashes=True)
def get_all_auctions():
    logger.info("###              DEMO: GET /dbproj/leiloes              ###");   

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, descricao FROM leilao WHERE fim > CURRENT_TIMESTAMP + '01:00'")
    rows = cur.fetchall()

    # idx_leilao_fim

    payload = []
    logger.debug("---- auctions  ----")
    for row in rows:
        logger.debug(row)
        content = {'leilaoId': int(row[0]), 'descricao': row[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

##
##  Pesquisar leiloes existentes
##  http://localhost:8080/dbproj/leiloes/abc
##

@app.route("/dbproj/leiloes/<keyword>", methods=['GET'])
def get_auction_by_keyword(keyword):
    logger.info("###              DEMO: GET /dbproj/leiloes/<keyword>              ###");   

    logger.debug(f'keyword: {keyword}')

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, descricao FROM leilao WHERE fim > CURRENT_TIMESTAMP  + '01:00' AND (artigo_ean = %s OR descricao LIKE %s)", (keyword, "%"+keyword+"%",) )
    rows = cur.fetchall()

    # idx_leilao_artigo_fim
    # idx_leilao_descricao_fim

    payload = []
    logger.debug("---- auction by keyword  ----")
    for row in rows:
        logger.debug(row)
        content = {'leilaoId': int(row[0]), 'descricao': row[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close ()
    return jsonify(payload)

##
##  Consultar detalhes de um leilao
##  http://localhost:8080/dbproj/leilao/1
##

@app.route("/dbproj/leilao/<leilaoId>", methods=['GET'])
def get_auction_by_id(leilaoId):
    logger.info("###              DEMO: GET /dbproj/leilao/<lailaoId>              ###");   

    logger.debug(f'leilaoId: {leilaoId}')

    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor() 

    cur.execute("SELECT id, descricao, titulo, fim, utilizador_username, artigo_ean FROM leilao WHERE id = %s", (leilaoId,) )

    # leilao_pkey

    rows = cur.fetchall()

    payload = []
    logger.debug("---- auction  ----")
    for row in rows:
        logger.debug(row)
        content = {'leilaoId': int(row[0]), 'descricao': row[1], 'titulo': row[2], 'fim': row[3], 'vendedor': row[4], 'artigo': row[5]}
        payload.append(content) # appending to the payload to be returned

    cur.execute("SELECT id, conteudo, instante, utilizador_username FROM mensagem WHERE leilao_id = %s", (leilaoId,) )

    # idx_mensagem_leilao_utilizador

    rows = cur.fetchall()

    messages = []
    logger.debug("---- messages  ----")
    for row in rows:
        logger.debug(row)
        content = {'mensagemId': int(row[0]), 'conteudo': row[1], 'instante': row[2], 'utilizador': row[3]}
        messages.append(content) # appending to the payload to be returned

    content = {'mensagens': messages} 
    payload.append(content)

    cur.execute("SELECT valor, utilizador_username, instante FROM licitacao WHERE leilao_id = %s", (leilaoId,) )

    # idx_licitacao_leilao_utilizador

    rows = cur.fetchall()

    bids = []
    logger.debug("---- bids  ----")
    for row in rows:
        logger.debug(row)
        content = {'valor': int(row[0]), 'utilizador': row[1], 'instante': row[2]}
        bids.append(content) # appending to the payload to be returned

    content = {'licitacoes': bids} 
    payload.append(content)

    conn.close ()
    return jsonify(payload)

##
##  Listar todos os leiloes	em que o utilizador tenha atividade
##  http://localhost:8080/dbproj/user/leiloes
##

@app.route("/dbproj/user/leiloes", methods=['GET'])
def get_auction_by_user():
    logger.info("###              DEMO: GET /dbproj/user/leiloes              ###");   

    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug("---- auction by user  ----")
    logger.debug(f'payload: {payload}')

    if "authToken" not in payload:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    # token validation
    cur.execute("SELECT username FROM utilizador WHERE authtoken = %s", (payload["authToken"],) )

    # utilizador_authtoken_key

    if int(cur.rowcount) == 0:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    username = cur.fetchone()[0]

    statement = """
                SELECT le.id, le.descricao
                    FROM leilao le
                    WHERE le.utilizador_username = %s or 
                    EXISTS 
                    (SELECT 
                        FROM mensagem me
                        WHERE me.leilao_id = le.id and me.utilizador_username = %s) or 
                    EXISTS 
                    (SELECT
                        FROM licitacao li 
                        WHERE li.leilao_id = le.id and li.utilizador_username = %s)"""

    # idx_memsagem_leilao_utilizador
    # idx_licitacao_leilao_utilizador

    values = (username, username, username, )

    cur.execute(statement, values )

    rows = cur.fetchall()

    payload = []
    for row in rows:
        logger.debug(row)
        content = {'leilaoId': int(row[0]), 'descricao': row[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close ()
    return jsonify(payload)

##
##  Efetuar	uma	licitacao num leilao
##  http://localhost:8080/dbproj/licitar/1/10
##

@app.route("/dbproj/licitar/<leilaoId>/<licitacao>", methods=['GET'])
def place_bid(leilaoId, licitacao):
    logger.info("###              DEMO: GET /dbproj/licitar/<leilaoId>/<licitacao>              ###");   

    logger.debug(f'leilaoId: {leilaoId}')
    logger.debug(f'licitacao: {licitacao}')

    payload = request.get_json()

    logger.debug("---- place bid  ----")
    logger.debug(f'payload: {payload}')


    conn = db_connection()
    cur = conn.cursor()

    if "authToken" not in payload:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    # concurrency control
    cur.execute("SELECT * FROM licitacao WHERE leilao_id = %s FOR UPDATE", (leilaoId,))
    cur.execute("SELECT * FROM leilao WHERE id = %s FOR UPDATE", (leilaoId,))

    statement = """
                INSERT INTO licitacao (valor, leilao_id, utilizador_username)
                SELECT %s,   %s,   username
                    FROM utilizador
                    WHERE authtoken = %s
                RETURNING leilao_id, valor"""

    # utilizador_authtoken_key

    values = (licitacao, leilaoId, payload["authToken"],)

    try:
        cur.execute(statement, values)
        if int(cur.rowcount) == 0:
            result = {'erro': 'AuthError'}
        else :
            row = cur.fetchone()
            cur.execute("commit")
            result = {'leilaoId': int(row[0]), 'valor': int(row[1])}
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'menssagem': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##
##  Editar leilao
##  http://localhost:8080/dbproj/leilao/4
##

@app.route("/dbproj/leilao/<leilaoId>", methods=['PUT'])
def edit_auction(leilaoId):
    logger.info("###              DEMO: PUT /dbproj/leilao/<leilaoId>             ###");   

    logger.debug(f'leilaoId: {leilaoId}')

    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- edit auction  ----")
    logger.info(f'content: {content}')

    if "authToken" not in content:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    if "titulo" not in content:
        if "descricao" not in content:
            return 'you must especify at least one attribute (titulo or descricao) to edit'
        else:
            statement ="""
                        UPDATE leilao
                        SET descricao = %s
                        WHERE id = %s AND utilizador_username = validate(%s)
                        RETURNING id, titulo, descricao, fim, utilizador_username, artigo_ean"""
            values = (content["descricao"], leilaoId, content["authToken"])
    else:
        if "descricao" not in content:
            statement ="""
                        UPDATE leilao
                        SET titulo = %s
                        WHERE id = %s AND utilizador_username = validate(%s)
                        RETURNING id, titulo, descricao, fim, utilizador_username, artigo_ean"""
            values = (content["titulo"], leilaoId, content["authToken"])
        else:
            statement ="""
                        UPDATE leilao
                        SET titulo = %s, descricao = %s
                        WHERE id = %s AND utilizador_username = validate(%s)
                        RETURNING id, titulo, descricao, fim, utilizador_username, artigo_ean"""
            values = (content["titulo"], content["descricao"], leilaoId, content["authToken"])

    # idx_leilao_pkey

    try:
        cur.execute(statement, values)

        row = cur.fetchone()
        cur.execute("commit")
        result = {'leilaoId': int(row[0]), 'titulo': row[1], 'descricao': row[2], 'fim': row[3], 'vendedor': row[4], 'artigo': row[5] }
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        if int(error.pgcode) == 18456:
            result = {'erro': 'AuthError'}
        else:
            result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(result)

##
##  Listar versoes
##  http://localhost:8080/dbproj/versoes/2
##

@app.route("/dbproj/versoes/<leilaoId>", methods=['GET'], strict_slashes=True)
def get_versions(leilaoId):
    logger.info("###              DEMO: GET /dbproj/versoes/<leilaoId>              ###");   

    logger.debug(f'leilaoId: {leilaoId}')

    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info(f'payload: {payload}')

    if "authToken" not in payload:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})
   
    # see if the user is the owner
    try:
        cur.execute("SELECT FROM leilao le WHERE le.id = %s AND le.utilizador_username = validate(%s)", (leilaoId, payload["authToken"], ) )
        if int(cur.rowcount) == 0:
            if conn is not None:
                conn.close()
            return jsonify({'erro': 'AuthError'})
    except (Exception, psycopg2.DatabaseError) as error:
        if conn is not None:
                conn.close()
        return jsonify({'erro': 'AuthError'})

    # idx_leilao_pkey

    cur.execute("SELECT id, titulo, descricao, instante FROM versao WHERE leilao_id = %s", (leilaoId, ))
    rows = cur.fetchall()

    # idx_versao_leilao

    payload = []
    logger.debug("---- vesoes  ----")
    for row in rows:
        logger.debug(row)
        content = {'versao': int(row[0]), 'titulo': row[1], 'descricao': row[2], 'instante': row[3] }
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

##
##  Escrever mensagem no mural de um leilao
##  http://localhost:8080/dbproj/mensagem/1
##

@app.route("/dbproj/mensagem/<leilaoId>", methods=['POST'])
def send_message(leilaoId):
    logger.info("###              DEMO: POST /dbproj/mensagem/<leilaoId>           ###");   

    logger.debug(f'leilaoId: {leilaoId}')

    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new message  ----")
    logger.debug(f'payload: {payload}')

    if "authToken" not in payload:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    if "conteudo" not in payload:
        if conn is not None:
            conn.close()
        return 'conteudo is required to send a message'

    statement = """
                INSERT INTO mensagem (conteudo, leilao_id, utilizador_username)
                SELECT %s,   %s ,   username
                    FROM utilizador
                    WHERE authtoken = %s
                RETURNING id"""

    # utilizador_authtoken_key

    values = (payload["conteudo"], leilaoId, payload["authToken"])

    try:
        cur.execute(statement, values)
        if int(cur.rowcount) == 0:
            result = {'erro': 'AuthError' }
        else :
            mensagemId = cur.fetchone()[0]
            cur.execute("commit")
            result = {'mensagemId': mensagemId}
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##
##  Listar notificacoes
##  http://localhost:8080/dbproj/notificacoes
##

@app.route("/dbproj/notificacoes", methods=['GET'])
def get_notifications():
    logger.info("###              DEMO: GET /dbproj/notificacoes              ###");

    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- notifications  ----")
    logger.debug(f'payload: {payload}')

    if "authToken" not in payload:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'})

    # token validation
    cur.execute("SELECT username FROM utilizador WHERE authtoken = %s", (payload["authToken"],) )

    # utilizador_authtoken_key
    
    if int(cur.rowcount) == 0:
        if conn is not None:
            conn.close()
        return jsonify({'erro': 'AuthError'}) 
        
    username = cur.fetchone()[0]

    statement = """
                SELECT me.id, me.conteudo, me.utilizador_username, me.instante
                    FROM mensagem_notificacao me_no, mensagem me
                    WHERE  me_no.mensagem_id = me.id and me_no.utilizador_username = %s"""
    
    cur.execute(statement, (username,) )

    # mensagem_notificacao_pkey

    rows = cur.fetchall()

    payload = []
    logger.debug("---- message notifications  ----")
    for row in rows:
        logger.debug(row)
        content = {'notoficacao': 'New message', 'memssagemId': int(row[0]), 'conteudo': row[1], 'username': row[2], 'instante': row[3]}
        payload.append(content) # appending to the payload to be returned

    statement = """
                SELECT li.leilao_id, li.valor, li.instante
                    FROM licitacao_notificacao li_no, licitacao li, licitacao li_ul
                    WHERE li_no.licitacao_leilao_id = li.leilao_id AND li_no.licitacao_valor = li.valor AND 
                    li_no.licitacao_ultrapassada_leilao_id = li_ul.leilao_id AND li_no.licitacao_ultrapassada_valor = li_ul.valor AND
                    li_ul.utilizador_username = %s"""

    cur.execute(statement, (username,) )

    # licitacao_notificacao_pkey
    # licitacao_ultrapassada_unique

    rows = cur.fetchall()

    logger.debug("---- bid notifications  ----")
    for row in rows:
        logger.debug(row)
        content = {'notificacao': 'You are losing', 'leilaoId': int(row[0]), 'valor': int(row[1]), 'instante': row[2]}
        payload.append(content) # appending to the payload to be returned

    conn.close ()
    return jsonify(payload)

##
##  Termino do leilao na data, hora e minuto marcados.
##  http://localhost:8080/dbproj/leiloes
##

@app.route("/dbproj/terminar/<leilaoId>", methods=['GET'], strict_slashes=True)
def close_auctions(leilaoId):
    logger.info("###              DEMO: GET /dbproj/leiloes/<leilaoId>              ###");   

    logger.debug(f'leilaoId: {leilaoId}')

    conn = db_connection()
    cur = conn.cursor()

    # concurrency control
    cur.execute("SELECT * FROM licitacao WHERE leilao_id = %s FOR UPDATE", (leilaoId,))

    logger.info("---- close auction  ----")
    try:
        cur.execute("SELECT close_leilao(%s)", (leilaoId,))
        vencedor = cur.fetchone()[0]
        if vencedor == None:
            logger.debug(vencedor)
            result = {'vencedor': 'No winner'}
        else:
            logger.debug(vencedor)
            result = {'vencedor': vencedor }
        cur.execute("commit")

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        logger.error(error)
        result = {'erro': error.pgcode, 'mensagem': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(user = "aulaspl",
                            password = "aulaspl",
                            host = "db",
                            port = "5432",
                            database = "dbfichas")
    return db


##########################################################
## MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    time.sleep(1) # just to let the DB start before this print :-)


    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.0 online: http://localhost:8080/dbproj/\n\n")


    

    app.run(host="0.0.0.0", debug=True, threaded=True)



