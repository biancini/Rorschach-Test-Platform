from gaesessions import delete_expired_sessions

def run():
    while not delete_expired_sessions():
        pass
