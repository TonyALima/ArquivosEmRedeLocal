import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from arquivos_em_rede_local.descoberta import Descoberta
from arquivos_em_rede_local.transferencia import Transferencia

class InterfaceGrafica:
    """
    Classe que representa a interface gráfica da aplicação de transferência de arquivos em rede local.
    """

    def __init__(self, name: str):
        """
        Inicializa a interface gráfica e os componentes de descoberta e transferência de arquivos.

        :param name: Nome do dispositivo local.
        """
        self.descoberta = Descoberta(name)
        self.descoberta.start_discovery_process()
        self.transferencia = Transferencia(self.solicitar_envio_arquivo)
        self.root = tk.Tk()
        self.root.title("Arquivos em Rede Local")
        self.create_widgets()

    def create_widgets(self):
        """
        Cria os widgets da interface gráfica, incluindo a árvore de dispositivos e os botões de ação.
        """
        self.tree = ttk.Treeview(self.root, columns=('Nome', 'IP'), show='headings')
        self.tree.heading('Nome', text='Nome')
        self.tree.heading('IP', text='IP')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.atualizar_btn = tk.Button(self.button_frame, text="Atualizar", command=self.atualizar_dispositivos)
        self.atualizar_btn.pack(fill=tk.X, pady=2)

        self.update_tree_and_buttons()

    def update_tree_and_buttons(self):
        """
        Atualiza a árvore de dispositivos conectados e os botões de envio de arquivos.
        """
        for widget in self.button_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget != self.atualizar_btn:
                widget.destroy()

        self.tree.delete(*self.tree.get_children())
        for dispositivo in self.descoberta.get_connected_devices():
            self.tree.insert('', tk.END, values=(dispositivo['name'], dispositivo['ip']))
            btn = tk.Button(self.button_frame, text=f"Enviar para {dispositivo['name']}", command=lambda d=dispositivo: self.enviar_para_dispositivo(d))
            btn.pack(fill=tk.X, pady=2)

    def enviar_para_dispositivo(self, dispositivo):
        """
        Abre um diálogo para selecionar um arquivo e envia o arquivo selecionado para o dispositivo especificado.

        :param dispositivo: Dicionário contendo as informações do dispositivo de destino.
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            print(f"Enviando {file_path} para {dispositivo['name']} ({dispositivo['ip']})")
            response = self.transferencia.send(file_path, dispositivo['ip'])
            messagebox.showinfo("Resposta", response)

    def atualizar_dispositivos(self):
        """
        Atualiza a lista de dispositivos conectados.
        """
        print("Atualizando dispositivos...")
        self.descoberta.reload()
        self.update_tree_and_buttons()

    def solicitar_envio_arquivo(self, ip, file_name):
        """
        Solicita ao usuário a permissão para receber um arquivo de um dispositivo remoto.

        :param ip: Endereço IP do dispositivo remoto.
        :param file_name: Nome do arquivo que está sendo solicitado para envio.
        :return: True se o usuário aceitar a solicitação, False caso contrário.
        """
        dispositivo = self.descoberta.get_device_by_ip(ip)
        if dispositivo is None:
            return False
        return messagebox.askyesno("Solicitação de Envio", f"{dispositivo['name']} ({dispositivo['ip']}) deseja enviar {file_name} para você. Deseja aceitar?")

    def run(self):
        """
        Inicia o loop principal da interface gráfica.
        """
        self.root.mainloop()

