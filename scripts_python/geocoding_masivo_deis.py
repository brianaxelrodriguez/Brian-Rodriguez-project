import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
import pandas as pd
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import ArcGIS, Nominatim

# --- RUTAS ---
BASE_DIR = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados"
FILE_FARMACIAS = os.path.join(BASE_DIR, "DEIS_Micro_Geo_Farmacias.csv")
FILE_HOSPITALES = os.path.join(BASE_DIR, "DEIS_Micro_Geo_Hospitales.csv")

# Inicializar Geocoders (Cascada)
geo_osm = Nominatim(user_agent="tesis_health_econ_argentina_v2", timeout=10)
geo_arcgis = ArcGIS(
    timeout=10
)  # Excelente alternativa a Google Maps para direcciones sucias


def armar_direccion(row):
    """Construye un string de búsqueda lógico para la API"""
    domicilio = str(row.get("DOMICILIO", "")).strip()
    localidad = str(row.get("LOCALIDAD", "")).strip()
    provincia = str(row.get("PROVINCIA", "")).strip()

    if domicilio.lower() in ["nan", "none", "s/n", "sin numero"]:
        domicilio = ""
    if localidad.lower() in ["nan", "none"]:
        localidad = ""

    partes = [p for p in [domicilio, localidad, provincia] if p]
    partes.append("Argentina")
    return ", ".join(partes)


class GeocoderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Geolocalizador DEIS (OSM + ArcGIS Fallback)")
        self.root.geometry("600x400")

        # Variables de control
        self.is_running = False
        self.is_paused = False
        self.thread = None
        self.total_registros = 0
        self.procesados = 0
        self.start_time = 0

        self.setup_ui()

    def setup_ui(self):
        # Estilos
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Segoe UI", 10))

        # Frame Principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Selección de archivo
        ttk.Label(
            main_frame,
            text="Seleccionar Base a Procesar:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=tk.W)
        self.target_var = tk.StringVar(value="Hospitales")
        ttk.Radiobutton(
            main_frame, text="Hospitales", variable=self.target_var, value="Hospitales"
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            main_frame, text="Farmacias", variable=self.target_var, value="Farmacias"
        ).pack(anchor=tk.W)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(20, 5))

        # Etiquetas de estado
        self.lbl_status = ttk.Label(main_frame, text="Estado: Esperando inicio...")
        self.lbl_status.pack(anchor=tk.W)

        self.lbl_stats = ttk.Label(
            main_frame, text="Procesados: 0 / 0 | Tiempo Est: --:--"
        )
        self.lbl_stats.pack(anchor=tk.W)

        # Log Text Box
        self.log_text = tk.Text(main_frame, height=8, state="disabled", bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        self.btn_start = ttk.Button(
            btn_frame, text="Iniciar", command=self.start_process
        )
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_pause = ttk.Button(
            btn_frame, text="Pausar", command=self.toggle_pause, state=tk.DISABLED
        )
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(
            btn_frame, text="Detener", command=self.stop_process, state=tk.DISABLED
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5)

    def log(self, message):
        """Agrega texto al recuadro de log"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    def start_process(self):
        if self.is_running:
            return

        archivo = (
            FILE_HOSPITALES if self.target_var.get() == "Hospitales" else FILE_FARMACIAS
        )
        if not os.path.exists(archivo):
            messagebox.showerror("Error", f"No se encuentra el archivo:\n{archivo}")
            return

        self.is_running = True
        self.is_paused = False
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL, text="Pausar")
        self.btn_stop.config(state=tk.NORMAL)
        self.log(f"Iniciando procesamiento de {self.target_var.get()}...")

        # Lanzar en hilo separado para no congelar la GUI
        self.thread = threading.Thread(
            target=self.run_geocoding, args=(archivo,), daemon=True
        )
        self.thread.start()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.config(text="Reanudar")
            self.log("[!] Proceso Pausado.")
        else:
            self.btn_pause.config(text="Pausar")
            self.log("[>] Proceso Reanudado.")

    def stop_process(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self.log("[!] Proceso detenido por el usuario.")

    def run_geocoding(self, ruta_archivo):
        df = pd.read_csv(ruta_archivo)

        if "LATITUD" not in df.columns:
            df["LATITUD"] = np.nan
        if "LONGITUD" not in df.columns:
            df["LONGITUD"] = np.nan

        mask_to_geocode = df["LATITUD"].isna() & (
            df["DOMICILIO"].notna() | df["LOCALIDAD"].notna()
        )
        indices_faltantes = df[mask_to_geocode].index.tolist()

        self.total_registros = len(indices_faltantes)
        self.procesados = 0
        self.start_time = time.time()

        if self.total_registros == 0:
            self.log("¡El archivo ya está 100% geolocalizado!")
            self.stop_process()
            return

        encontrados_osm = 0
        encontrados_arcgis = 0

        for idx in indices_faltantes:
            if not self.is_running:
                break
            while self.is_paused:
                time.sleep(0.5)

            row = df.loc[idx]
            query = armar_direccion(row)

            if query.count(",") < 2:
                df.at[idx, "LATITUD"] = 0.0
                df.at[idx, "LONGITUD"] = 0.0
                self.guardar_fila(df, ruta_archivo)  # GUARDADO A 1
                self.actualizar_progreso()
                continue

            try:
                # 1er Intento: OpenStreetMap
                location = geo_osm.geocode(query)
                origen = "OSM"

                # 2do Intento (Fallback): ArcGIS (Suele ser mejor para zonas rurales/sucias)
                if not location:
                    location = geo_arcgis.geocode(query)
                    origen = "ArcGIS"

                if location:
                    df.at[idx, "LATITUD"] = location.latitude
                    df.at[idx, "LONGITUD"] = location.longitude
                    if origen == "OSM":
                        encontrados_osm += 1
                    else:
                        encontrados_arcgis += 1
                    self.log(
                        f"[OK - {origen}] {query[:35]}... -> ({location.latitude:.4f}, {location.longitude:.4f})"
                    )
                else:
                    df.at[idx, "LATITUD"] = 0.0
                    df.at[idx, "LONGITUD"] = 0.0
                    self.log(f"[NO HALLADO] {query[:40]}...")

            except (GeocoderTimedOut, GeocoderUnavailable):
                self.log("[!] Timeout API. Esperando 5s...")
                time.sleep(5)
            except Exception as e:
                self.log(f"[!] Error: {str(e)[:50]}")

            # GUARDADO ESTRICTO DE A 1 REGISTRO (Persistencia absoluta)
            self.guardar_fila(df, ruta_archivo)

            # Rate limiting ético (ArcGIS permite más, pero OSM requiere 1 seg)
            time.sleep(1.2)
            self.actualizar_progreso()

        self.log(
            f"\nFinalizado. Exitos OSM: {encontrados_osm} | Exitos ArcGIS: {encontrados_arcgis}"
        )
        self.stop_process()

    def guardar_fila(self, df, ruta_archivo):
        # Guardar en disco inmediatamente
        df.to_csv(ruta_archivo, index=False)

    def actualizar_progreso(self):
        self.procesados += 1
        pct = (self.procesados / self.total_registros) * 100
        self.progress_var.set(pct)

        # Calcular tiempo estimado restante (ETA)
        elapsed = time.time() - self.start_time
        vel = elapsed / self.procesados
        restante_seg = vel * (self.total_registros - self.procesados)
        m, s = divmod(restante_seg, 60)
        h, m = divmod(m, 60)
        eta_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

        self.lbl_status.config(text=f"Estado: Procesando... ({pct:.1f}%)")
        self.lbl_stats.config(
            text=f"Procesados: {self.procesados} / {self.total_registros} | Tiempo Est: {eta_str}"
        )


# Arranque de la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = GeocoderApp(root)
    root.mainloop()
