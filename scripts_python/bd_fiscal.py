import datetime
import os
import tarfile
import zipfile

# Intentar importar rarfile (requiere 'pip install rarfile' y unrar en el sistema)
try:
    import rarfile

    HAS_RAR = True
except ImportError:
    HAS_RAR = False


def explorar_data_raw():
    directorio_raiz = r"C:\Users\brian\Documents\Proyectos_IA\data_raw"
    archivo_salida = os.path.join(directorio_raiz, "inventario_data_raw.txt")

    if not os.path.exists(directorio_raiz):
        print(f"Error: El directorio {directorio_raiz} no existe.")
        return

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(f"INVENTARIO DATA RAW - Generado el {datetime.datetime.now()}\n")
        f.write("=" * 80 + "\n\n")

        for root, _, files in os.walk(directorio_raiz):
            # Evitar entrar en carpetas generadas por el script u otros outputs
            if "inventario_data_raw.txt" in files:
                files.remove("inventario_data_raw.txt")

            for file in files:
                ruta_completa = os.path.join(root, file)
                ruta_relativa = os.path.relpath(ruta_completa, directorio_raiz)
                ext = os.path.splitext(file)[1].lower()

                f.write(f"Archivo: {ruta_relativa}\n")
                f.write(f"Tipo/Extensión: {ext if ext else 'Sin extensión'}\n")

                # Procesar archivos comprimidos
                if ext == ".zip":
                    try:
                        with zipfile.ZipFile(ruta_completa, "r") as zip_ref:
                            archivos_internos = zip_ref.namelist()
                            f.write("  Contenido ZIP:\n")
                            for interno in archivos_internos[
                                :20
                            ]:  # Limitar a 20 para no saturar
                                f.write(f"    - {interno}\n")
                            if len(archivos_internos) > 20:
                                f.write(
                                    f"    ... y {len(archivos_internos) - 20} archivos más.\n"
                                )
                    except zipfile.BadZipFile:
                        f.write("  [Error: Archivo ZIP corrupto o no válido]\n")

                elif ext in [".tar", ".gz", ".tgz", ".bz2", ".xz"]:
                    try:
                        with tarfile.open(ruta_completa, "r:*") as tar_ref:
                            archivos_internos = tar_ref.getnames()
                            f.write("  Contenido TAR/GZ:\n")
                            for interno in archivos_internos[:20]:
                                f.write(f"    - {interno}\n")
                            if len(archivos_internos) > 20:
                                f.write(
                                    f"    ... y {len(archivos_internos) - 20} archivos más.\n"
                                )
                    except tarfile.TarError:
                        f.write("  [Error: Archivo TAR/GZ corrupto o no válido]\n")

                elif ext == ".rar":
                    if HAS_RAR:
                        try:
                            with rarfile.RarFile(ruta_completa, "r") as rar_ref:
                                archivos_internos = rar_ref.namelist()
                                f.write("  Contenido RAR:\n")
                                for interno in archivos_internos[:20]:
                                    f.write(f"    - {interno}\n")
                                if len(archivos_internos) > 20:
                                    f.write(
                                        f"    ... y {len(archivos_internos) - 20} archivos más.\n"
                                    )
                        except rarfile.Error:
                            f.write(
                                "  [Error: Archivo RAR corrupto o falta unrar en el sistema]\n"
                            )
                    else:
                        f.write(
                            "  [Aviso: Archivo RAR detectado. Instalar librería 'rarfile' para ver contenido]\n"
                        )

                f.write("-" * 40 + "\n")

    print(f"Inventario finalizado. Revisa el archivo: {archivo_salida}")


explorar_data_raw()
