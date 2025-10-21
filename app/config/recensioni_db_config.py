# Configurazione DB MySQL (host = nome servizio docker nella rete)
DB_CONFIG = {
    'user': 'user',
    'password': '123',
    'host': 'mysql_db',    # hostname del container mysql nella rete docker
    'database': 'recensioni_db',
    'raise_on_warnings': True
}