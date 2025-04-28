import torch
import numpy as np
import cv2
import time
import win32api
import pandas as pd
import os
import datetime
import requests
from utils.general import (cv2, non_max_suppression, xyxy2xywh)


from config import exitnuz, layartinggi, confidence, displayframe, visuals
import pilihjendela


ID_KELAS_ORANG = 0  
TOKEN_BOT_TELEGRAM = "7750932128:AAEiR5294p6rAPxweyak6_4ezHrKVy9CLew"  
ID_CHAT_TELEGRAM = "1254913051"  
DIREKTORI_SCREENSHOT = "C:/Users/Acer/Pictures/Nitro"  
INTERVAL_LAPORAN = 3600  


os.makedirs(DIREKTORI_SCREENSHOT, exist_ok=True)


def kirim_pesan_telegram(pesan, path_gambar=None):
    try:
        if path_gambar and os.path.exists(path_gambar):
            url = f"https://api.telegram.org/bot{TOKEN_BOT_TELEGRAM}/sendPhoto"
            with open(path_gambar, 'rb') as foto:
                files = {'photo': foto}
                data = {'chat_id': ID_CHAT_TELEGRAM, 'caption': pesan}
                response = requests.post(url, files=files, data=data)
        else:
            url = f"https://api.telegram.org/bot{TOKEN_BOT_TELEGRAM}/sendMessage"
            data = {'chat_id': ID_CHAT_TELEGRAM, 'text': pesan}
            response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Gagal kirim pesan telegram (cek koneksi): {e}")
        return None


def simpan_screenshot(frame, prefix="deteksi"):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nama_file = f"{DIREKTORI_SCREENSHOT}/{prefix}_{timestamp}.jpg"
    cv2.imwrite(nama_file, frame)
    return nama_file

class MonitorStream:
    def __init__(self):
        self.data_afk = []
        self.apakah_orang_terlihat = True
        self.mulai_afk_sekarang = None
        self.waktu_mulai = time.time()
        self.waktu_laporan_terakhir = time.time()
        
        
        kirim_pesan_telegram("+++ OJOAFK by NUZ ♥️ +++")
    
    def perbarui_status_afk(self, apakah_terlihat, frame):
        waktu_sekarang = time.time()
        
        
        if not apakah_terlihat and self.apakah_orang_terlihat:
            self.apakah_orang_terlihat = False
            self.mulai_afk_sekarang = waktu_sekarang
            
            
            path_screenshot = simpan_screenshot(frame, "afk_terdeteksi")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            kirim_pesan_telegram(f"AFK! {timestamp}", path_screenshot)
        
     
        elif apakah_terlihat and not self.apakah_orang_terlihat:
            self.apakah_orang_terlihat = True
            
            if self.mulai_afk_sekarang:
                durasi = waktu_sekarang - self.mulai_afk_sekarang
                
                
                self.data_afk.append({
                    "waktu_mulai": self.mulai_afk_sekarang,
                    "waktu_selesai": waktu_sekarang,
                    "durasi": durasi
                })
                
                
                menit, detik = divmod(durasi, 60)
                kirim_pesan_telegram(f"AFK SELAMA {int(menit)} MENIT {int(detik)} DETIK!")
    
    def cek_waktu_laporan(self):
        waktu_sekarang = time.time()
        if waktu_sekarang - self.waktu_laporan_terakhir >= INTERVAL_LAPORAN:
            self.kirim_laporan()
            self.waktu_laporan_terakhir = waktu_sekarang
    
    def kirim_laporan(self):
        
        detik_berjalan = time.time() - self.waktu_mulai
        jam, sisa = divmod(detik_berjalan, 3600)
        menit, detik = divmod(sisa, 60)
        
       
        total_waktu_afk = sum(record["durasi"] for record in self.data_afk)
        jam_afk, sisa_afk = divmod(total_waktu_afk, 3600)
        menit_afk, detik_afk = divmod(sisa_afk, 60)
        
       
        pesan = (
            f"+++ LAPORAN OJOAFK +++\n\n"
            f"Durasi pemantauan: {int(jam)}Jam {int(menit)}Menit {int(detik)}Detik\n\n"
            f"AFK terdeteksi: {len(self.data_afk)} kali\n"
            f"All time: {int(jam_afk)}Jam {int(menit_afk)}Menit {int(detik_afk)}Detik\n"
        )
        
        kirim_pesan_telegram(pesan)

def utama():
    
    kamera, lebar, tinggi = pilihjendela.pilihjendela()
    
    
    monitor = MonitorStream()
    
    hitung = 0
    waktu_mulai = time.time()

    
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s',
                           pretrained=True, force_reload=True)
    stride, names, pt = model.stride, model.names, model.pt

    if torch.cuda.is_available():
        model.half()
    
    WARNA = (255, 255, 255)

    koordinat_tengah_terakhir = None
    with torch.no_grad():
        while win32api.GetAsyncKeyState(ord(exitnuz)) == 0:
            
            npImg = np.array(kamera.get_latest_frame())

            im = torch.from_numpy(npImg)
            if im.shape[2] == 4:
                im = im[:, :, :3]

            im = torch.movedim(im, 2, 0)
            if torch.cuda.is_available():
                im = im.half()
                im /= 255
            if len(im.shape) == 3:
                im = im[None]

            
            hasil = model(im, size=layartinggi)

            
            prediksi = non_max_suppression(
                hasil, confidence, confidence, 0, False, max_det=1000)

            
            orang_terdeteksi = False
            
            target = []
            for i, det in enumerate(prediksi):
                s = ""
                gn = torch.tensor(im.shape)[[0, 0, 0, 0]]
                if len(det):
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()
                        s += f"{n} {names[int(c)]}, "
                        
                        
                        if int(c) == ID_KELAS_ORANG:
                            orang_terdeteksi = True

                    for *xyxy, conf, cls in reversed(det):
                        target.append((xyxy2xywh(torch.tensor(xyxy).view(
                            1, 4)) / gn).view(-1).tolist() + [float(conf), int(cls)]) 

            
            if target:
                target = pd.DataFrame(
                    target, columns=['tengah_x_sekarang', 'tengah_y_sekarang', 'lebar', "tinggi", "confidence", "class"])
            else:
                target = pd.DataFrame(
                    columns=['tengah_x_sekarang', 'tengah_y_sekarang', 'lebar', "tinggi", "confidence", "class"])

            
            monitor.perbarui_status_afk(orang_terdeteksi, npImg)
            monitor.cek_waktu_laporan()

            

            if visuals:
                
                for i in range(0, len(target)):
                    setengah_lebar = round(target["lebar"][i] / 2)
                    setengah_tinggi = round(target["tinggi"][i] / 2)
                    tengah_x = target['tengah_x_sekarang'][i]
                    tengah_y = target['tengah_y_sekarang'][i]
                    (startX, startY, endX, endY) = int(
                        tengah_x + setengah_lebar), int(tengah_y + setengah_tinggi), int(tengah_x - setengah_lebar), int(tengah_y - setengah_tinggi)
                    
                  
                    warna_kotak = WARNA
                    id_kelas = int(target['class'][i])
                    
                    if id_kelas == ID_KELAS_ORANG:
                        warna_kotak = (255, 255, 255)  
                    
                    cv2.rectangle(npImg, (startX, startY), (endX, endY), warna_kotak, 2)
                    
                    y_teks = startY - 15 if startY - 15 > 15 else startY + 15
                    y_persentase = y_teks + 20
                    
                 
                    if id_kelas == ID_KELAS_ORANG:
                        label = "NUZ"
                    else:
                        label = names[id_kelas] if id_kelas < len(names) else f"Kelas {id_kelas}"
                    
                    cv2.putText(npImg, f" {label} ", (startX, y_teks),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, warna_kotak, 2)
                    
                    cv2.putText(npImg, f" {target['confidence'][i] * 100:.2f}% ", (startX, y_persentase),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, warna_kotak, 2)      
                
                teks_status = []
                if not monitor.apakah_orang_terlihat:
                    durasi = time.time() - monitor.mulai_afk_sekarang
                    menit, detik = divmod(durasi, 60)
                    teks_status.append(f"AFK terlihat selama {int(menit)}Menit {int(detik)}Detik")
                
                
                for idx, teks in enumerate(teks_status):
                    cv2.putText(npImg, teks, (10, 30 + 30*idx),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            
            hitung += 1
            if (time.time() - waktu_mulai) > 1:
                if displayframe:
                    print("{} Frame per Detik".format(hitung))
                hitung = 0
                waktu_mulai = time.time()

            
            if visuals:
                cv2.imshow('ZUNUZZZ', npImg)
                if (cv2.waitKey(1) & 0xFF) == ord('q'):
                    
                    monitor.kirim_laporan()
                    exit()
                    
    
    kamera.stop()
    
    monitor.kirim_laporan()

if __name__ == "__main__":
    try:
        utama()
    except Exception as e:
        import traceback
        traceback.print_exception(e)
        print("ERROR! " + str(e))
        
        
        pesan_error = f"OJOAFK error... {str(e)}\ntanya @zunuzzz"
        kirim_pesan_telegram(pesan_error)
        
        print("Tekan apa saja untuk keluar...")
        input()