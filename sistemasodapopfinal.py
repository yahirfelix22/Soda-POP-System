import tkinter as tk
import customtkinter as ctk
import pygame
from PIL import Image, ImageTk, ImageDraw, ImageOps
import threading
import time
from collections import deque
import random

# --- CONFIGURACIÓN DE RUTAS ---
# Rutas de archivos multimedia (música y fondo de pantalla)
RUTA_MUSICA = r"C:\Users\yahir balderrama\Contacts\Downloads\music.mp3\_Soda Pop_ Official Lyric Video _ KPop Demon Hunters _ Sony Animation [983bBbJx0Mk].wav"
RUTA_FONDO = r"C:\Users\yahir balderrama\Contacts\Downloads\music.mp3\kpop-demon-hunters-saja-boys-4k-wallpaper-uhdpaper.com-650@5@f.jpg"

# =========================================================
# LÓGICA DEL KERNEL (Núcleo del Sistema)
# =========================================================
class KernelSaja:
    """
    Clase que simula el núcleo del sistema operativo.
    Maneja la creación de procesos y el algoritmo de planificación Round Robin.
    """
    def __init__(self, gui_callback):
        self.cola_listos = deque()      # Cola de procesos esperando ejecución
        self.proceso_actual = None      # Proceso que está en la CPU actualmente
        self.lista_historica = []       # Registro de todos los procesos creados
        self.contador_pid = 1000        # Generador de ID de procesos
        self.quantum = 3                # Tiempo máximo de ejecución por turno (segundos)
        self.running = True             # Estado del kernel
        self.gui_callback = gui_callback # Función para actualizar la interfaz visual

    def crear_proceso(self, nombre):
        """Crea un nuevo proceso con un tiempo de vida aleatorio y lo añade a la cola."""
        pid = self.contador_pid
        nuevo = {"pid": pid, "nombre": nombre.upper(), "tiempo": random.randint(5, 12), "estado": "LISTO"}
        self.cola_listos.append(nuevo)
        self.lista_historica.append(nuevo)
        self.contador_pid += 1
        self.gui_callback()

    def eliminar_proceso(self, pid):
        """Busca un proceso por PID y lo marca como TERMINADO."""
        if self.proceso_actual and self.proceso_actual['pid'] == pid:
            self.proceso_actual = None
        self.cola_listos = deque([p for p in self.cola_listos if p['pid'] != pid])
        for p in self.lista_historica:
            if p['pid'] == pid:
                p['estado'] = "TERMINADO"
        self.gui_callback()

    def planificador_rr(self):
        """
        Algoritmo de Planificación Round Robin.
        Asigna la CPU a cada proceso durante un tiempo definido (Quantum).
        """
        while self.running:
            if self.cola_listos:
                # Extrae el primer proceso de la cola
                self.proceso_actual = self.cola_listos.popleft()
                self.proceso_actual["estado"] = "EJECUTANDO"
                self.gui_callback()
                
                # Ejecuta por el tiempo del quantum o hasta que el proceso termine
                for _ in range(min(self.quantum, self.proceso_actual["tiempo"])):
                    if not self.running or not self.proceso_actual: break
                    time.sleep(1)
                    self.proceso_actual["tiempo"] -= 1
                
                # Reingresa a la cola si aún tiene tiempo restante, de lo contrario termina
                if self.proceso_actual:
                    self.proceso_actual["estado"] = "LISTO" if self.proceso_actual["tiempo"] > 0 else "TERMINADO"
                    if self.proceso_actual["estado"] == "LISTO":
                        self.cola_listos.append(self.proceso_actual)
                self.proceso_actual = None
                self.gui_callback()
            time.sleep(0.5)

# =========================================================
# INTERFAZ SAJAOS (Capa de Presentación)
# =========================================================
class SajaOS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.attributes("-fullscreen", True) # Pantalla completa
        self.title("SajaOS - Hunter System")
        
        # Inicialización del Kernel en un hilo secundario para no congelar la ventana
        self.kernel = KernelSaja(self.refrescar_terminal)
        threading.Thread(target=self.kernel.planificador_rr, daemon=True).start()
        
        # Inicialización de audio con Pygame
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(RUTA_MUSICA)
            pygame.mixer.music.play(-1) # Reproducción infinita
        except: pass

        # Canvas para el fondo de pantalla
        self.canvas_fondo = tk.Canvas(self, highlightthickness=0)
        self.canvas_fondo.pack(fill="both", expand=True)
        self.update() 
        self.cargar_login()

    def cargar_login(self):
        """Dibuja la pantalla de inicio de sesión con el fondo y avatar."""
        try:
            img_original = Image.open(RUTA_FONDO)
            img_res = img_original.resize((self.winfo_screenwidth(), self.winfo_screenheight()), Image.Resampling.LANCZOS)
            self.fondo_tk = ImageTk.PhotoImage(img_res)
            self.canvas_fondo.create_image(0, 0, image=self.fondo_tk, anchor="nw")

            # Creación del avatar circular
            saja_face = img_original.crop((450, 100, 650, 300)) 
            size = 180
            mask = Image.new('L', (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            saja_face = saja_face.resize((size, size))
            circular_saja = ImageOps.fit(saja_face, (size, size), centering=(0.5, 0.5))
            circular_saja.putalpha(mask)
            
            self.avatar_tk = ImageTk.PhotoImage(circular_saja)
            cx, cy = self.winfo_screenwidth() // 2, self.winfo_screenheight() // 2
            self.avatar_id = self.canvas_fondo.create_image(cx, cy - 120, image=self.avatar_tk)
            self.text_id = self.canvas_fondo.create_text(cx, cy, text="Saja Hunter", font=("Segoe UI Semibold", 38), fill="white")
        except:
            self.canvas_fondo.config(bg="#050505")

        # Formulario de entrada (Contraseña)
        cx, cy = self.winfo_screenwidth() // 2, self.winfo_screenheight() // 2
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_fondo.create_window(cx, cy + 100, window=self.login_frame)
        self.entry_pass = ctk.CTkEntry(self.login_frame, placeholder_text="Contraseña", show="*", width=280)
        self.entry_pass.grid(row=0, column=0)
        ctk.CTkButton(self.login_frame, text="→", width=40, command=self.iniciar_sesion).grid(row=0, column=1, padx=5)

    def iniciar_sesion(self):
        """Limpia la pantalla de login e inicia el escritorio."""
        self.login_frame.destroy()
        if hasattr(self, 'avatar_id'): self.canvas_fondo.delete(self.avatar_id)
        if hasattr(self, 'text_id'): self.canvas_fondo.delete(self.text_id)
        self.dibujar_escritorio()

    def mostrar_acerca_de(self):
        """Muestra una ventana emergente con datos del equipo Soda POP."""
        ventana = ctk.CTkToplevel(self)
        ventana.title("Acerca de Soda POP")
        ventana.geometry("600x550")
        ventana.configure(fg_color="#0a0a0a")
        ventana.attributes("-topmost", True)

        ctk.CTkLabel(ventana, text="SISTEMA SODA POP", font=("Segoe UI", 28, "bold"), text_color="#00fbff").pack(pady=20)
        
        info = ("Este sistema gestiona procesos mediante el algoritmo de planificación Round Robin.\n"
                "Monitorea cambios de estado (Listo, Ejecutando, Terminado) en tiempo real\n"
                "y simula la interacción del Kernel con Entrada/Salida.")
        ctk.CTkLabel(ventana, text=info, font=("Segoe UI", 12), wraplength=500).pack(pady=10)

        ctk.CTkLabel(ventana, text="INTEGRANTES", font=("Segoe UI", 18, "bold"), text_color="#ff007f").pack(pady=15)
        
        integrantes = [
            "Jaziel Josue Aranda Carreras       279565",
            "Laura Fernanda López Carrizosa     280677",
            "Karolina Ramos Taylor              278714",
            "Yahir Alexis Felix Balderrama      281636"
        ]
        
        for persona in integrantes:
            ctk.CTkLabel(ventana, text=persona, font=("Consolas", 14)).pack(pady=3)

        ctk.CTkButton(ventana, text="Cerrar", fg_color="#333", hover_color="#444", command=ventana.destroy).pack(pady=30)

    def dibujar_escritorio(self):
        """Configura la barra de tareas y el área de trabajo."""
        # --- BARRA DE TAREAS ---
        self.bar = ctk.CTkFrame(self, width=int(self.winfo_screenwidth()*0.98), height=65, fg_color="#0a0a0a", corner_radius=15, border_width=1, border_color="#1a1a1a")
        self.bar.place(relx=0.5, rely=0.93, anchor="center")
        
        # Botones funcionales e informativos de la barra
        self.btn_gestion = ctk.CTkButton(self.bar, text="⚙ Gestión de Procesos", width=180, height=40, fg_color="#00fbff", text_color="black", font=("Segoe UI", 12, "bold"), command=self.toggle_gestor)
        self.btn_gestion.pack(side="left", padx=10)

        ctk.CTkButton(self.bar, text="📊 Estados", width=100, fg_color="transparent", text_color="#ff007f", command=lambda: self.log_terminal("INFO: Consultando estados...")).pack(side="left", padx=5)
        ctk.CTkButton(self.bar, text="🕒 Planificación: RR", width=140, fg_color="transparent", text_color="#00fbff", command=lambda: self.log_terminal(f"KERNEL: Round Robin Q={self.kernel.quantum}s")).pack(side="left", padx=5)
        ctk.CTkButton(self.bar, text="⌨ Comandos", width=100, fg_color="transparent", text_color="white", command=lambda: self.ejecutar_terminal_manual("ayuda")).pack(side="left", padx=5)
        ctk.CTkButton(self.bar, text="🔌 I/O", width=80, fg_color="transparent", text_color="#aaff00", command=self.simular_io).pack(side="left", padx=5)

        # Botón Acerca de
        self.btn_about = ctk.CTkButton(self.bar, text="ℹ Acerca de", width=110, fg_color="#1f1f1f", text_color="white", font=("Segoe UI", 11, "bold"), command=self.mostrar_acerca_de)
        self.btn_about.pack(side="left", padx=10)

        # Botón de Apagado
        ctk.CTkButton(self.bar, text="Cerrar Sistema", width=110, height=35, fg_color="#222", text_color="white", hover_color="#ff4444", command=self.quit).pack(side="right", padx=15)

        # --- VENTANA TERMINAL (Oculta por defecto) ---
        self.frame_proc = ctk.CTkFrame(self, width=700, height=550, fg_color="#050505", border_width=2, border_color="#00fbff")
        self.frame_proc.pack_propagate(False)
        self.gestor_visible = False

        self.txt_terminal = ctk.CTkTextbox(self.frame_proc, width=660, height=420, fg_color="#000000", text_color="#00fbff", font=("Consolas", 13))
        self.txt_terminal.pack(pady=15)
        self.txt_terminal.insert("end", "SajaOS Hunter System [Version 2.0]\nKernel en linea. Escriba 'ayuda' para comenzar.\n" + "="*50 + "\n")

        self.entry_cmd = ctk.CTkEntry(self.frame_proc, placeholder_text="root@saja:~$ ", width=660, height=35, border_color="#00fbff")
        self.entry_cmd.pack(pady=5)
        self.entry_cmd.bind("<Return>", lambda e: self.ejecutar_terminal_manual())

    def toggle_gestor(self):
        """Muestra u oculta la terminal de procesos."""
        if not self.gestor_visible:
            self.frame_proc.place(relx=0.5, rely=0.45, anchor="center")
            self.gestor_visible = True
            self.entry_cmd.focus()
        else:
            self.frame_proc.place_forget()
            self.gestor_visible = False

    def log_terminal(self, mensaje):
        """Imprime un mensaje rápido en la terminal."""
        if not self.gestor_visible: self.toggle_gestor()
        self.txt_terminal.insert("end", f"\n>> {mensaje}\n")
        self.txt_terminal.see("end")

    def simular_io(self):
        """Simula una operación de Entrada/Salida."""
        self.log_terminal("I/O: Detectando dispositivos... Teclado y Monitor listos.")
        print("\n[MODO I/O] Ingrese dato en consola:")
        threading.Thread(target=lambda: print(f"I/O Recibido: {input('> ')}"), daemon=True).start()

    def ejecutar_terminal_manual(self, comando_directo=None):
        """Procesa los comandos ingresados por el usuario."""
        raw_input = comando_directo if comando_directo else self.entry_cmd.get().strip()
        if not raw_input: return
        
        self.txt_terminal.insert("end", f"\nroot@saja:~$ {raw_input}\n")
        args = raw_input.split()
        cmd = args[0].lower()

        if cmd == "crear" and len(args) > 1:
            self.kernel.crear_proceso(args[1])
        elif cmd == "kill" and len(args) > 1:
            try: self.kernel.eliminar_proceso(int(args[1]))
            except: self.log_terminal("Error: PID no válido")
        elif cmd == "ayuda":
            self.txt_terminal.insert("end", "\n-- COMANDOS --\n> crear [nombre]\n> kill [pid]\n> limpiar\n")
        elif cmd == "limpiar":
            self.txt_terminal.delete("1.0", "end")
        
        if not comando_directo: self.entry_cmd.delete(0, 'end')
        self.refrescar_terminal()

    def refrescar_terminal(self):
        """Actualiza la tabla de procesos visual en la terminal."""
        if hasattr(self, 'txt_terminal'):
            content = self.txt_terminal.get("1.0", "end")
            tag = "[--- MONITOR DE PROCESOS ---]"
            
            # Reemplaza la tabla anterior para evitar duplicados
            if tag in content:
                idx = content.find(tag)
                self.txt_terminal.delete(f"1.0 + {idx} chars", "end")
            
            # Construcción de la tabla
            tabla = f"\n{tag}\n{'PID':<6} | {'NOMBRE':<15} | {'TIME':<4} | {'ESTADO'}\n" + "-"*45 + "\n"
            for p in self.kernel.lista_historica:
                # Puntero visual para identificar el proceso en ejecución
                puntero = ">> " if self.kernel.proceso_actual and p['pid'] == self.kernel.proceso_actual['pid'] else "    "
                tabla += f"{p['pid']:<6} | {p['nombre']:<15} | {p['tiempo']:<4} | {puntero}{p['estado']}\n"
            
            self.txt_terminal.insert("end", tabla)
            self.txt_terminal.see("end")

# Punto de entrada de la aplicación
if __name__ == "__main__":
    app = SajaOS()
    app.mainloop()