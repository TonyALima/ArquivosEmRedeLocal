from arquivos_em_rede_local.visualizacao import InterfaceGrafica
import socket
import getpass

def main():
    username = f'{getpass.getuser()}:{socket.gethostname()}'
    app = InterfaceGrafica(username)
    app.run()

if __name__ == "__main__":
    main()