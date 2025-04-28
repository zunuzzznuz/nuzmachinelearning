import pygetwindow
import time
import bettercam
from typing import Union


from config import layartinggi, layarlebar

def pilihjendela() -> (bettercam.BetterCam, int, Union[int, None]):
    
    try:
        semua_jendela = pygetwindow.getAllWindows()
        print("++++++ NUZ ++++++")
        for indeks, jendela in enumerate(semua_jendela):
            
            if jendela.title != "":
                print("[{}]: {}".format(indeks, jendela.title))
        
        try:
            pilihan_user = int(input(
                "Masukkan nomor jendela yang ingin dipilih. Bingung? Tanya melalui https://steamcommunity.com/id/zunuzzz\nNomor : "))
        except ValueError:
            print("Nomor tidak valid! Silakan coba lagi.")
            return None
        
        jendelapilihan = semua_jendela[pilihan_user]
    except Exception as e:
        print("GAGAL! (masukan nomor jendela) {}".format(e))
        return None


    percobaan_aktivasi = 30
    berhasil_aktivasi = False
    while (percobaan_aktivasi > 0):
        try:
            jendelapilihan.activate()
            berhasil_aktivasi = True
            break
        except pygetwindow.PyGetWindowException as we:
            print("BUKA JENDELA PILIHAN! {}".format(str(we)))
            print("COBA LAGI! atau tanya https://steamcommunity.com/id/zunuzzz")
        except Exception as e:
            print("BUKA JENDELA PILIHAN! {}".format(str(e)))
            print("BACA DOKUMENTASI https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow")
            berhasil_aktivasi = False
            percobaan_aktivasi = 0
            break
        
        time.sleep(3.0)
        percobaan_aktivasi = percobaan_aktivasi - 1
    
    if not berhasil_aktivasi:
        return None
    print("JENDELA BERHASIL DIAKTIFKAN!")

    
    kiri = ((jendelapilihan.left + jendelapilihan.right) // 2) - (layarlebar // 2)
    atas = jendelapilihan.top + (jendelapilihan.height - layartinggi) // 2
    kanan, bawah = kiri + layarlebar, atas + layartinggi

    area: tuple = (kiri, atas, kanan, bawah)

    
    lebar: int = layarlebar // 2
    tinggi: int = layartinggi // 2

    print(area)

    kamera = bettercam.create(region=area, output_color="BGRA", max_buffer_len=512)
    if kamera is None:
        print("GAGAL MEMULAI KAMERA! TANYA MELALUI https://steamcommunity.com/id/zunuzzz")
        return None
    kamera.start(target_fps=120, video_mode=True)

    return kamera, lebar, tinggi