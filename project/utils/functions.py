def get_credential_type(value):
    if '@' in value:
        credential_type = 'endereço de email'
    else:
        credential_type = 'número de telefone'
    return credential_type