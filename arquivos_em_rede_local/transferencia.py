import socket
import threading

class Transferencia:
    def __init__(self, get_user_authorization, transfer_port=23009):
        self.transfer_port = transfer_port
        self.running_listener = True
        self.listen_to_incoming_requests_thread = threading.Thread(target=self._listen_to_incoming_requests, daemon=True)
        self.listen_to_incoming_requests_thread.start()
        self.get_user_authorization = get_user_authorization

    def __del__(self):
        self.running_listener = False
        if self.listen_to_incoming_requests_thread.is_alive():
            self.listen_to_incoming_requests_thread.join()

    def send(self, file_path, device_ip):
        try:
            with open(file_path, 'rb') as file:
                data = file.read()
        except Exception as e:
            return "Failed to get file: " + str(e)

        with socket.create_connection((device_ip, self.transfer_port)) as sock:
            if self._request_send_authorization(sock, file_path):
                sock.sendall(data)
                sock.sendall(b'End of file')
                return "File sent successfully"
            else:
                return "Failed to send file: Authorization denied"

    def _request_send_authorization(self, sock: socket.socket, file_path):
        file_name = file_path.split('/')[-1]
        message = f"SEND {file_name}"
        sock.sendall(message.encode())
        sock.settimeout(60)
        try:
            response = sock.recv(1024).decode()
            return response == "OK"
        except Exception:
            return False

    def _listen_to_incoming_requests(self):
        with socket.create_server(('', self.transfer_port)) as sock:
            sock.settimeout(1)
            while self.running_listener:
                try:
                    conn, addr = sock.accept()
                    data = conn.recv(1024)
                    if data.decode().startswith('SEND'):
                        file_name = data.decode().split(' ')[1]
                        if self.get_user_authorization(addr[0], file_name):
                            conn.sendall("OK".encode())
                            self._receive_and_save_file(conn, file_name)
                        else:
                            conn.sendall("NO".encode())
                    conn.close()
                except socket.timeout:
                    continue

    def _receive_and_save_file(self, conn: socket.socket, file_name):
        data = b''
        conn.settimeout(1)
        while True:
            try:
                data += conn.recv(1024)
                if data.endswith(b'End of file'):
                    data = data[:-len(b'End of file')]
                    break
            except socket.timeout:
                break
        if data:
            with open(file_name, 'wb') as file:
                file.write(data)
        else:
            print("Failed to receive file")

# Example usage:
# transferencia = Transferencia()
# transferencia.send('/path/to/file', '192.168.1.2')