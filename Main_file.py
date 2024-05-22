import asyncio
from asyncio import AbstractEventLoop
from queue import Queue
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from threading import Thread
from typing import Callable
from typing import Optional, Union

from parser_file import Image_Parser
from install import Image_Installer

TITLE = 'Python Pictures Scraper'
SIZE = (420, 460)

from validators import (validate_picture_amount,
                        check_saving_path,
                        has_picture_amount_been_chosen,
                        is_picture_amount_positive_int)

class UI(tk.Tk):
    #Основное окно приложения
    def __init__(self, title: str, size: tuple[int],
                 first_loop: AbstractEventLoop,
                 second_loop: AbstractEventLoop) -> None:
        # Настройки основного окна
        super().__init__() # создание главного окна приложения
        self.title(title)
        self.geometry(f'{size[0]}x{size[1]}')
        self.resizable(False, False)
        self.title("Image search application")

        self.first_loop: AbstractEventLoop = first_loop
        self.loop_for_saves: AbstractEventLoop = second_loop
        self.__links_array: set[str] = set()
        self.picture_name: str = ''
        #Создание объекта класса SearchFrame
        self.search_frame = SearchFrame(
            parent=self,
            links_array=self.links_array,
            set_picture_name=self.set_picture_name,
            first_loop=self.first_loop,
            update_parsing_frame_data=self.update_parsing_frame_data
            )
        # Создание объекта класса ScraperFrame
        self.parsing_frame = ScraperFrame(
            parent=self,
            links_array=self.links_array,
            get_picture_name=self.get_picture_name,
            second_loop=self.loop_for_saves)

    # Возвращает значение __links_array
    @property
    def links_array(self):
        return self.__links_array
    # Устанавливает новое значение __links_array
    @links_array.setter
    def links_array(self, links_array):
        self.__links_array = links_array

    def update_parsing_frame_data(self) -> None:
        pictures_amount = len(self.links_array)
        self.parsing_frame.pictures_amount_var.set(pictures_amount)
        self.parsing_frame.pictures_spin_box.configure(to=pictures_amount)
        self.parsing_frame.progress_bar['value'] = 0

    def get_picture_name(self) -> None:
        return self.picture_name

    def set_picture_name(self, picture_name) -> None:
        self.picture_name = picture_name


class SearchFrame(ttk.Frame):
    def __init__(self, parent: UI, links_array: set[str],
                 set_picture_name: Callable, first_loop: AbstractEventLoop,
                 update_parsing_frame_data: Callable) -> None:

        super().__init__(parent)
        self.first_loop: AbstractEventLoop = first_loop
        self.update_parsing_frame_data: Callable = update_parsing_frame_data
        self.links_array: set[str] = links_array
        self.set_picture_name: Callable = set_picture_name

        self.pack(expand=True, fill='both', pady=30) #упаковка в родительский контейнер
        self.search_data = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
            # Создание метки и поля ввода

            self.search_label = ttk.Label(self, text="Enter your request", style="Head.TLabel", font=("Arial Bold", 16), background="#D3D3D3")
            self.search_entry = ttk.Entry(self, textvariable=self.search_data, style="Input.TEntry")

            find_button = ttk.Button(self, text="Search", command=self.get_links, style="PrimaryButton.TButton")
            reset_button = ttk.Button(self, text="Reset List", command=self.clear_array_of_links,
                                      style="SecondaryButton.TButton")

            # Размещение элементов интерфейса
            self.search_label.place(x=125, y=-5)
            self.search_entry.place(x=150, y=25)
            find_button.place(x=65, y=50)
            reset_button.place(x=275, y=50)

    # clear_array_of_links Очищает массив links_array. Обновляет данные в фрейме для парсинга, вызывая метод update_parsing_frame_data.
    def clear_array_of_links(self) -> None:
        self.links_array.clear()
        self.update_parsing_frame_data()
    # Устанавливает имя картинки, запускает парсер
    def get_links(self) -> None:
        self.set_picture_name(self.search_entry.get())
        links = Image_Parser(first_loop, self.add_links, self.get_entry_data())
        links.start()
    #Добавляет новую ссылку в массив links_array.
    def add_links(self, link) -> None:
        self.links_array.add(link)
        self.update_parsing_frame_data()
    #Возвращает данные, введенные в поле ввода
    def get_entry_data(self) -> str:
        return self.search_data.get()


class ScraperFrame(ttk.Frame):
    def __init__(self, parent: UI, links_array: set[str],
                 get_picture_name: Callable,
                 second_loop: AbstractEventLoop) -> None:
        super().__init__(parent)
        self.links_array: set[str] = links_array
        self.second_loop: AbstractEventLoop = second_loop
        self.queue: Queue = Queue()
        self.refresh_ms = 25
        self.get_picture_name: Callable = get_picture_name

        self.load_saver: Optional[Union[None, Image_Installer]] = None

        self.pack(expand=True, fill='both', padx=10)

        self.rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self.columnconfigure((0, 1, 2), weight=1)

        self.pictures_amount_var = tk.IntVar()
        self.folder_path_var = tk.StringVar()
        self.radio_var = tk.IntVar(value=0)
        self.status_message = tk.StringVar(value='Operation status')

        self.create_widgets()

    def create_widgets(self) -> None:
        found_label = ttk.Label(self, text='Found: ')
        pictures_amount_label = ttk.Label(
            self,
            textvariable=self.pictures_amount_var
            )
        pictures_caption_label = ttk.Label(self, text='images')
        path_label = ttk.Label(self, text='The saving path: ')
        self.path_entry = ttk.Entry(self, textvariable=self.folder_path_var,
                                    state='readonly', width=25)
        path_button = ttk.Button(self, text='...',
                                 command=self.open_folder_dialog)
        number_of_images = ttk.Label(self, text='Number of images: ')
        self.pictures_spin_box = ttk.Spinbox(self, from_=1, width=30)
        self.start_button = ttk.Button(self, text='Start',
                                       command=self.start_scraper)
        self.progress_bar = ttk.Progressbar(self, orient='horizontal',
                                            mode='determinate')
        status_message_label = ttk.Label(self,
                                         textvariable=self.status_message)

        found_label.grid(row=0, column=0, pady=10)
        pictures_amount_label.grid(row=0, column=1)
        pictures_caption_label.grid(row=0, column=2)
        path_label.grid(row=1, column=0, pady=10)
        self.path_entry.grid(row=1, column=1)
        path_button.grid(row=1, column=2)
        number_of_images.grid(row=3, column=0, pady=10)
        self.pictures_spin_box.grid(row=3, column=1, columnspan=2, ipadx=10)
        self.start_button.grid(row=4, column=1, pady=5, sticky='w')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky='nswe')
        status_message_label.grid(row=6, column=0, columnspan=3, pady=5)

    def start_scraper(self) -> None:
        pictures_spin_amount = 0 if not self.pictures_spin_box.get() \
            else int(self.pictures_spin_box.get())
        picture_name = self.get_picture_name()
        if not check_saving_path(self.path_entry.get()):
            self.status_message.set('Select the path to save')
        elif not has_picture_amount_been_chosen(pictures_spin_amount):
            self.status_message.set('The number of images to save is not selected')
        elif not is_picture_amount_positive_int(pictures_spin_amount):
            self.status_message.set('The number of images cannot be zero')
        elif not validate_picture_amount(pictures_spin_amount,
                                           self.links_array):
            self.status_message.set(
                f'The number of images cannot exceed {len(self.links_array)}'
                )
        else:
            self.status_message.set('')
            self.total_requests = int(self.pictures_spin_box.get())
            pictures_mode = self.radio_var.get()
            save_path = self.path_entry.get()
            if self.load_saver is None:
                self.start_button['text'] = 'Cancel'
                self.status_message.set('Saving is in progress...')
                saver = Image_Installer(
                    loop=self.second_loop,
                    links_array=self.links_array,
                    picture_name=picture_name,
                    save_path=save_path,
                    total_requests=self.total_requests,
                    callback=self.update_queue)
                self.after(self.refresh_ms, self.check_queue)
                saver.start()
                self.load_saver = saver
            else:
                self.status_message.set('The operation was canceled')
                self.load_saver.cancel()
                self.load_saver = None
                self.start_button['text'] = 'Start'

    def update_progress_bar(self, progress_percent: int) -> None:
        if progress_percent == 100:
            self.progress_bar['value'] = 100
            self.load_saver = None
            self.pictures_spin_box.delete(0, 'end')
            self.status_message.set('Images have been saved successfully')
            self.links_array.clear()
            pictures_amount = len(self.links_array)
            self.pictures_amount_var.set(pictures_amount)
            self.pictures_spin_box.configure(to=pictures_amount)
            self.start_button['text'] = 'Start'
        else:
            self.progress_bar['value'] = progress_percent
            self.after(self.refresh_ms, self.check_queue)

    def update_queue(self, completed_requests: int,
                     total_requests: int) -> None:
        self.queue.put(int(completed_requests * 100 / total_requests))

    def check_queue(self) -> None:
        if not self.queue.empty():
            percent_complete = self.queue.get()
            self.update_progress_bar(percent_complete)
        else:
            if self.load_saver:
                if self.total_requests > 1:
                    self.after(self.refresh_ms, self.check_queue)
                else:
                    self.after(self.refresh_ms, self.check_queue)
                    self.update_progress_bar(100)

    def open_folder_dialog(self) -> None:
        folder_path = filedialog.askdirectory()
        self.folder_path_var.set(folder_path)


class ThreadedEventLoop(Thread):
    def __init__(self, first_loop: AbstractEventLoop):
        super().__init__()
        self._loop: AbstractEventLoop = first_loop
        self.daemon: bool = True

    def run(self) -> None:
        self._loop.run_forever()

if __name__ == '__main__':
    first_loop = asyncio.new_event_loop()
    second_loop = asyncio.new_event_loop()

    asyncio_thread = ThreadedEventLoop(first_loop)
    asyncio_thread.start()

    asyncio_thread_saver = ThreadedEventLoop(second_loop)
    asyncio_thread_saver.start()

    app = UI(TITLE, SIZE, first_loop, second_loop)
    app.mainloop()
