import cv2
import pyzbar.pyzbar as pyzbar
import json
import base64
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import configparser
import os


config = configparser.ConfigParser()
config.read("conf.ini")

class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.show_start_screen()
        self.root.mainloop()

    def show_start_screen(self):
        """Показать стартовый экран"""
        # Остановить все активные процессы сканирования
        self.stop_scanning()

        # Очистить текущее содержимое
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("RDP QR Scanner")
        self.root.geometry("400x400")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)

        # Центрирование окна
        self.center_window(400, 400)

        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Логотип
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((190, 104), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(main_frame, image=self.logo_photo, bg='#f0f0f0')
            logo_label.pack(pady=(0, 10))
        except Exception as e:
            print(f"Ошибка загрузки логотипа: {e}")
            # Заглушка если лого не найдено
            no_logo_label = tk.Label(
                main_frame,
                text="Логотип",
                font=("Arial", 14),
                bg='#f0f0f0',
                fg='#999'
            )
            no_logo_label.pack(pady=(0, 10))

        # Заголовок
        title_label = tk.Label(
            main_frame,
            text="Сканер QR-кодов для RDP",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#333'
        )
        title_label.pack(pady=(0, 5))

        # Описание
        desc_label = tk.Label(
            main_frame,
            text="Приложение для подключения к удалённому рабочему столу\nчерез QR-код с учётными данными",
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#666',
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 20))

        # Кнопка "Начать"
        start_btn = ttk.Button(
            main_frame,
            text="Начать сканирование",
            command=self.start_scanning,
            width=20,
            style="Start.TButton"
        )
        start_btn.pack(pady=(10, 10))

        # Настройка стилей
        style = ttk.Style()
        style.configure("Start.TButton", font=("Arial", 12), padding=10)

    def center_window(self, width, height):
        """Центрирование окна на экране"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def start_scanning(self):
        """Запуск сканирования"""
        # Очистить текущее содержимое
        for widget in self.root.winfo_children():
            widget.destroy()

        # Настроить окно для сканирования
        self.root.title("RDP QR Scanner - Сканирование")
        self.root.geometry("800x600")
        self.root.configure(bg='black')
        self.root.resizable(False, False)
        self.center_window(800, 600)

        # Загрузка шрифта
        self.load_fonts()

        # Переменные состояния
        self.scanning = True
        self.last_qr_data = None
        self.rdp_process = None
        self.rdp_active = False
        self.connection_status = tk.StringVar()
        self.connection_status.set("Готов к сканированию")

        # Создание интерфейса
        self.create_scanner_widgets()

        # Настройка камеры
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.show_error("Не удалось открыть камеру")
            return

        # Установка разрешения камеры
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Запуск потока для обработки видео
        self.thread = threading.Thread(target=self.process_video, daemon=True)
        self.thread.start()

    def load_fonts(self):
        """Загрузка шрифтов для русского текста"""
        # Попытка загрузить русский шрифт
        self.russian_font = None
        try:
            # Проверяем доступные шрифты
            possible_fonts = [
                "DejaVuSans.ttf",
                "arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"
            ]

            for font_path in possible_fonts:
                if os.path.exists(font_path):
                    self.russian_font = ImageFont.truetype(font_path, 20)
                    break

            # Если не нашли, используем стандартный
            if not self.russian_font:
                print("Русский шрифт не найден, будет использован стандартный")
                self.russian_font = ImageFont.load_default()
        except Exception as e:
            print(f"Ошибка загрузки шрифта: {e}")
            self.russian_font = ImageFont.load_default()

    def create_scanner_widgets(self):
        """Создание интерфейса для сканирования"""
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg="black")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Верхняя панель статуса
        status_frame = tk.Frame(main_frame, bg="#333", height=40)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(status_frame, textvariable=self.connection_status,
                 font=("Arial", 12), fg="white", bg="#333").pack(side=tk.LEFT, padx=10)

        # Контейнер для видео с фиксированными размерами
        video_container = tk.Frame(main_frame, bg="black", width=640, height=480)
        video_container.pack(pady=(0, 10))
        video_container.pack_propagate(False)

        # Видео лейбл
        self.video_label = tk.Label(video_container, bg="black")
        self.video_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Кнопка отмены
        button_frame = tk.Frame(main_frame, bg="black")
        button_frame.pack(fill=tk.X, pady=(5, 0))

        # Центрируем кнопку
        btn_container = tk.Frame(button_frame, bg="black")
        btn_container.pack(expand=True)

        ttk.Button(btn_container, text="Вернуться", command=self.return_to_start,
                   width=15, style="TButton").pack(pady=10)

        # Настройка стилей
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 12), padding=6)

    def return_to_start(self):
        """Возврат на стартовый экран с остановкой сканирования"""
        self.stop_scanning()
        self.show_start_screen()

    def stop_scanning(self):
        """Остановка сканирования и освобождение ресурсов"""
        self.scanning = False

        # Остановить камеру
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

        # Подождать завершения потока
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        # Сбросить флаги
        self.rdp_active = False

    def process_video(self):
        while self.scanning and self.cap.isOpened():
            # Пропускаем обработку кадров, если активно RDP-подключение
            if self.rdp_active:
                time.sleep(1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            frame = cv2.resize(frame, (640, 480))
            frame = cv2.flip(frame, 1)

            # Конвертируем в PIL Image для работы с текстом
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)

            # Рисуем текст
            text = "Поместите QR-код сюда"
            try:
                # Получаем размеры текста
                if self.russian_font and hasattr(self.russian_font, 'getsize'):
                    text_width, text_height = self.russian_font.getsize(text)
                else:
                    # Для стандартного шрифта
                    text_width, text_height = 200, 20
            except:
                text_width, text_height = 200, 20

            # Координаты рамки
            frame_size = 300
            x = (640 - frame_size) // 2
            y = (480 - frame_size) // 2

            # Рисуем текст
            try:
                if self.russian_font:
                    draw.text(((640 - text_width) // 2, y - text_height - 10),
                              text, font=self.russian_font, fill=(255, 0, 0))
                else:
                    draw.text(((640 - 200) // 2, y - 30),
                              "Place QR code here", fill=(255, 0, 0))
            except:
                # Если не получилось с русским шрифтом
                draw.text(((640 - 200) // 2, y - 30),
                          "Place QR code here", fill=(255, 0, 0))

            # Рисуем рамку
            draw.rectangle([x, y, x + frame_size, y + frame_size],
                           outline=(255, 0, 0), width=2)

            # Распознавание QR-кодов только в целевой области
            roi = frame[y:y + frame_size, x:x + frame_size]

            decoded_objects = pyzbar.decode(roi)

            # Обработка распознанных QR-кодов
            if decoded_objects and not self.rdp_active:
                obj = decoded_objects[0]
                qr_data = obj.data.decode("utf-8")

                try:
                    # Парсинг JSON
                    json_data = json.loads(qr_data)
                    username = json_data.get("username", "")
                    base64_pwd = json_data.get("password", "")

                    if username and base64_pwd:
                        # Декодирование пароля
                        password = base64.b64decode(base64_pwd).decode("utf-8")

                        # Запуск RDP в отдельном потоке
                        if qr_data != self.last_qr_data:
                            self.last_qr_data = qr_data
                            self.connection_status.set("Подключаемся...")
                            threading.Thread(
                                target=self.connect_rdp,
                                args=(username, password),
                                daemon=True
                            ).start()

                except Exception as e:
                    self.connection_status.set(f"Ошибка: {str(e)}")

            # Конвертация для Tkinter
            img = ImageTk.PhotoImage(image=pil_img)

            # Обновление видео в основном потоке
            if self.scanning:  # Проверяем, что сканирование еще активно
                self.root.after(0, self.update_video, img)

            # Задержка для снижения нагрузки на CPU
            time.sleep(0.03)

        # Освобождение ресурсов
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def update_video(self, img):
        """Обновление видео"""
        # Проверяем, что виджет еще существует
        if hasattr(self, 'video_label') and self.video_label.winfo_exists():
            self.video_label.configure(image=img)
            self.video_label.image = img

    def connect_rdp(self, username, password):
        try:
            self.rdp_active = True

            # Останавливаем сканирование
            self.stop_scanning()

            # Формирование команды подключения
            cmd = [
                "xfreerdp",
                f"/v:{config["RDP_Settings"]["RDP_SERVER"]}:{config["RDP_Settings"]["RDP_PORT"]}",
                f"/u:{config["RDP_Settings"]["DOMAIN"]}\\{username}",
                f"/p:{password}",
                f"/w:{config["RDP_Settings"]["WIDTH"]}",
                f"/h:{config["RDP_Settings"]["HEIGHT"]}",
                "+clipboard",
                "/cert:ignore",
                "/rfx"
            ]

            # Запуск RDP клиента
            self.connection_status.set("Подключение активно...")
            self.rdp_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Ожидание завершения RDP-сессии
            self.rdp_process.wait()

        except Exception as e:
            self.connection_status.set(f"Ошибка: {str(e)}")
        finally:
            # После завершения RDP возвращаемся к стартовому окну
            self.rdp_active = False
            self.root.after(0, self.show_start_screen)

    def show_error(self, message):
        error_label = tk.Label(self.root, text=message, fg="red", bg="black", font=("Arial", 14))
        error_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


if __name__ == "__main__":
    app = Application()