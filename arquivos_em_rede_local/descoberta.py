import socket
import threading

class Descoberta:
    """
    Classe para descoberta e comunicação de dispositivos em uma rede local.

    Atributos:
        my_name (str): Nome do dispositivo.
        discovery_port (int): Porta usada para descoberta de dispositivos.
        comunication_port (int): Porta usada para comunicação entre dispositivos.
        descobertas (list): Lista de endereços IP descobertos.
        dispositivos (list): Lista de dispositivos conectados.
        running_discovery (bool): Flag para indicar se a descoberta está em execução.
        running_comunication (bool): Flag para indicar se a comunicação está em execução.
        discovery_listener_thread (threading.Thread): Thread para escutar mensagens de descoberta.
        comunication_thread (threading.Thread): Thread para iniciar a comunicação com dispositivos descobertos.
    """

    def __init__(self, my_name, discovery_port=14810, comunication_port=7736):
        """
        Inicializa a classe Descoberta.

        Args:
            my_name (str): Nome do dispositivo.
            discovery_port (int, optional): Porta usada para descoberta de dispositivos. Padrão é 14810.
            comunication_port (int, optional): Porta usada para comunicação entre dispositivos. Padrão é 7736.
        """
        self.my_name = my_name
        self.discovery_port = discovery_port
        self.comunication_port = comunication_port
        self.descobertas = []
        self.dispositivos = []
        self.running_discovery = False
        self.running_comunication = False
        self.discovery_listener_thread = threading.Thread(target=self.listen_for_discovery_messages, daemon=True)
        self.comunication_thread = threading.Thread(target=self.initiate_communication, daemon=True)
        self.listen_for_responses_thread = threading.Thread(target=self.listen_for_responses, daemon=True)

    def __del__(self):
        """
        Finaliza a classe Descoberta, parando a descoberta e a comunicação.
        """
        self.listen_for_responses_thread.join()
        self.stop_discovery_listener()
        self.stop_communication()

    def stop_discovery_listener(self):
        """
        Para a descoberta de dispositivos.
        """
        if self.running_discovery:
            self.running_discovery = False
            self.discovery_listener_thread.join()

    def stop_communication(self):
        """
        Para a comunicação com dispositivos.
        """
        if self.running_comunication:
            self.running_comunication = False
            self.comunication_thread.join()

    def broadcast_discovery_message(self):
        """
        Envia uma mensagem de descoberta para a rede local.
        """
        mensagem = b'Discovery: Who is out there?'
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(mensagem, ('<broadcast>', self.discovery_port))
        sock.close()

    def listen_for_discovery_messages(self):
        """
        Escuta mensagens de descoberta na rede local.
        """
        self.running_discovery = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.discovery_port))
        
        while self.running_discovery:
            sock.settimeout(1)
            try:
                dados, endereco = sock.recvfrom(1024)
                if dados.decode() == 'Discovery: Who is out there?':
                    self.descobertas.append(endereco[0])
                    if not self.running_comunication:
                        self.comunication_thread.start()
            except socket.timeout:
                continue
        sock.close()

    def send_discovery_response(self, sock: socket.socket):
        """
        Envia uma resposta para um dispositivo que enviou uma mensagem de descoberta.

        Args:
            sock (socket.socket): Socket de comunicação.
        """
        mensagem = b'I am here!'
        try:
            sock.sendall(mensagem)
        except Exception as e:
            print(f"Erro ao enviar resposta: {e}")

    def receive_device_name(self, sock: socket.socket):
        """
        Recebe o nome de um dispositivo.

        Args:
            sock (socket.socket): Socket de comunicação.

        Returns:
            str: Nome do dispositivo, ou None se não for possível receber o nome.
        """
        try:
            data = sock.recv(1024)
            if data:
                message = data.decode()
                if message.startswith("My name is "):
                    return message[len("My name is "):]
        except Exception as e:
            print(f"Erro ao receber nome: {e}")
            return None
        return None

    def send_device_name(self, sock: socket.socket):
        """
        Envia o nome do dispositivo para outro dispositivo.

        Args:
            sock (socket.socket): Socket de comunicação.
        """
        mensagem = f"My name is {self.my_name}"
        try:
            sock.sendall(mensagem.encode())
        except Exception as e:
            print(f"Erro ao enviar nome: {e}")

    def initiate_communication(self):
        """
        Inicia a comunicação com dispositivos descobertos.
        """
        self.running_comunication = True
        for ip in self.descobertas:
            if not any(dispositivo['ip'] == ip for dispositivo in self.dispositivos):
                try:
                    sock = socket.create_connection((ip, self.comunication_port))
                    self.send_discovery_response(sock)
                    name = self.receive_device_name(sock)
                    if name:
                        self.send_device_name(sock)
                        self.dispositivos.append({
                            'ip': ip,
                            'name': name
                        })
                    sock.close()
                except Exception as e:
                    print(f"Erro conectar com {ip}: {e}")
            self.descobertas.remove(ip)
        self.running_comunication = False

    def handle_discovery_response(self, ip, sock: socket.socket):
        """
        Trata a resposta de um dispositivo descoberto.

        Args:
            ip (str): Endereço IP do dispositivo.
            sock (socket.socket): Socket de comunicação.
        """
        if not any(dispositivo['ip'] == ip for dispositivo in self.dispositivos):
            self.send_device_name(sock)
            name = self.receive_device_name(sock)
            if name:
                self.dispositivos.append({
                    'ip': ip,
                    'name': name
                })
        sock.close()

    def listen_for_responses(self):
        """
        Escuta respostas de dispositivos na rede local.
        """
        threads = []
        sock = socket.create_server(('', self.comunication_port))
        sock.settimeout(3)
        recived = True
        while recived:
            try:
                conn, addr = sock.accept()
                data = conn.recv(1024)
                if data.decode() == 'I am here!':
                    t = threading.Thread(target=self.handle_discovery_response, args=(addr[0], conn,), daemon=True)
                    t.start()
                    threads.append(t)
            except socket.timeout:
                recived = False
        for t in threads:
            t.join()
        sock.close()

    def start_discovery_process(self):
        """
        Inicia o processo de descoberta de dispositivos na rede local.
        """
        # Envia a mensagem de descoberta
        self.broadcast_discovery_message()
        self.listen_for_responses_thread.start()
        
        # Inicia a escuta de outras descobertas em uma thread separada
        self.discovery_listener_thread.start()

    
    def get_connected_devices(self):
        """
        Retorna a lista de dispositivos conectados.

        Returns:
            list: Lista de dispositivos conectados.
        """
        return self.dispositivos
