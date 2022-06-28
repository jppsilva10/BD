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
