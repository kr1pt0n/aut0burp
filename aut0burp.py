#!/usr/bin/env python3

import os
import re
import stat
import subprocess
import sys  # <--- Agregamos esto para poder borrar y actualizar la línea de la barra
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

DOWNLOAD_PAGE = "https://portswigger.net/burp/downloads"


def obtener_version_y_url():
    html = requests.get(DOWNLOAD_PAGE, headers=HEADERS).text

    match = re.search(r"burpsuite_linux_v(\d+)_(\d+)_(\d+)\.sh", html)

    if not match:
        print("[-] No se pudo detectar la versión.")
        return None

    version = ".".join(match.groups())

    download_url = (
        "https://portswigger.net/burp/releases/download"
        f"?product=desktop&version={version}&type=Linux"
    )

    print(f"[+] Versión detectada: {version}")
    print(f"[+] URL: {download_url}")

    return version, download_url


def descargar(url, version):
    filename = f"burpsuite_linux_v{version.replace('.', '_')}.sh"

    # 1. Quitamos el print normal y usamos sys.stdout.write sin salto de línea
    sys.stdout.write(f"[+] Descargando: {filename} ")
    sys.stdout.flush()

    r = requests.get(url, headers=HEADERS, stream=True, allow_redirects=True)
    r.raise_for_status()

    # Obtenemos el tamaño total del archivo que manda el servidor
    total_size = int(r.headers.get("content-length", 0))
    descargado = 0

    with open(filename, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
                descargado += len(chunk)  # Sumamos los bytes que van llegando

                # Si el servidor nos dio el tamaño, calculamos la barra real
                if total_size > 0:
                    porcentaje = (descargado / total_size) * 100
                    bloques = int(30 * descargado / total_size)

                    # 2. Con \r volvemos al inicio y volvemos a pintar tu mensaje más la barra al lado
                    sys.stdout.write(
                        f"\r[+] Descargando: {filename} [{'█' * bloques}{'.' * (30 - bloques)}] {porcentaje:.1f}%"
                    )
                    sys.stdout.flush()

    # Damos un salto de línea al terminar la barra
    print()

    size = os.path.getsize(filename)
    print(f"[+] Descargado OK ({size / (1024*1024):.2f} MB)")

    return filename


def dar_permisos(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)
    print("[+] Permisos de ejecución asignados")


def ejecutar(filename):
    print("[+] Ejecutando instalador...")
    subprocess.run(["sudo", f"./{filename}"], check=True)


def main():
    data = obtener_version_y_url()

    if not data:
        return

    version, url = data

    archivo = descargar(url, version)

    dar_permisos(archivo)

    opcion = input("\n¿Ejecutar instalador? (s/n): ").lower().strip()

    if opcion == "s":
        ejecutar(archivo)
    else:
        print("[+] Instalador descargado sin ejecutar")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[+] Operación cancelada por el usuario")
    except requests.RequestException as e:
        print(f"\n[-] Error de red: {e}")
