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
        self.local_ip = self.get_local_ip()
        self.descobertas = []
        self.dispositivos = []
        self.running_discovery = False
        self.running_comunication = False
        self.discovery_listener_thread = threading.Thread(target=self.listen_for_discovery_messages, daemon=True)
        self.comunication_thread = threading.Thread(target=self.initiate_communication, daemon=True)
        self.listen_for_responses_thread = threading.Thread(target=self.listen_for_responses, daemon=True)
        self.verify_devices_alive_thread = threading.Thread(target=self.verify_devices_alive, daemon=True)

    def __del__(self):
        """
        Finaliza a classe Descoberta, parando a descoberta e a comunicação.
        """
        if self.listen_for_responses_thread.is_alive():
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

    def get_local_ip(self):
        """
        Obtém o endereço IP local do dispositivo.

        Returns:
            str: Endereço IP local.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Não precisa se conectar de fato, apenas obter o IP local
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def broadcast_discovery_message(self):
        """
        Envia uma mensagem de descoberta para a rede local.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for _ in range(3):
            mensagem = b'Discovery: Who is out there?'
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
                data, addr = sock.recvfrom(1024)
                if data.decode() == 'Discovery: Who is out there?':
                    self.descobertas.append(addr[0])
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
            if (not any(dispositivo['ip'] == ip for dispositivo in self.dispositivos)
                and ip != self.local_ip):
                try:
                    with socket.create_connection((ip, self.comunication_port)) as sock:
                        self.send_discovery_response(sock)
                        name = self.receive_device_name(sock)
                        if name:
                            self.send_device_name(sock)
                            self.dispositivos.append({
                                'ip': ip,
                                'name': name
                            })
                except Exception as e:
                    print(f"Erro conectar com {ip}: {e}")
            self.descobertas.remove(ip)
        self.running_comunication = False
        self.comunication_thread = threading.Thread(target=self.initiate_communication, daemon=True)

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

    def reload(self):
        """
        Reenvia a mensagem de descoberta para tentar descobrir novos dispositivos.
        """

        
        if not self.running_discovery:
            self.start_discovery_process()
        elif not self.listen_for_responses_thread.is_alive():
            self.broadcast_discovery_message()
            self.listen_for_responses_thread = threading.Thread(target=self.listen_for_responses, daemon=True)
            self.listen_for_responses_thread.start()
        
        if not self.verify_devices_alive_thread.is_alive():
            self.verify_devices_alive_thread = threading.Thread(target=self.verify_devices_alive, daemon=True)
            self.verify_devices_alive_thread.start()

    def get_connected_devices(self):
        """
        Retorna a lista de dispositivos conectados.

        Returns:
            list: Lista de dispositivos conectados.
        """
        return self.dispositivos

    def verify_devices_alive(self):
        """
        Envia uma mensagem para todos os dispositivos descobertos e verifica se ainda estão na rede.
        """
        message = "Hello, are you there?"
        def send_message(dispositivo):
            try:
                with socket.create_connection((dispositivo['ip'], self.comunication_port), timeout=5) as sock:
                    sock.sendall(message.encode())
                    response = sock.recv(1024)
                    if not response:
                        self.dispositivos.remove(dispositivo)
            except Exception:
                self.dispositivos.remove(dispositivo)
        threads = []
        for dispositivo in self.dispositivos:
            t = threading.Thread(target=send_message, args=(dispositivo,), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def get_device_by_ip(self, ip):
        """
        Retorna um dispositivo da lista de dispositivos conectados pelo seu IP.

        Args:
            ip (str): Endereço IP do dispositivo.

        Returns:
            dict: Dispositivo com o IP fornecido, ou None se não for encontrado.
        """
        for dispositivo in self.dispositivos:
            if dispositivo['ip'] == ip:
                return dispositivo
        return None
