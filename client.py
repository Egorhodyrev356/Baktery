import socket
import time

import pygame
import math
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
from pygame import font



buffer = 1024


def login():
    global name
    name = row.get()
    if name and color:
        root.destroy()
        root.quit()
    else:
        tk.messagebox.showerror('Ошибка', 'Не выбрано имя или цвет')


def scroll(event):
    global color
    color = combo.get()
    style.configure('TCombobox', fieldbackground=color,
                    background='white')

def find(vector: str):
    global buffer
    first = vector.find('<')
    second = vector.find('>')
    if first < second or first >= 0:
        result = vector[first + 1:second]
        return result
    buffer = int(buffer * 1.5)
    return ""

def draw_bakteries(data: list[str]):
    for bact in data:
        data = bact.split(' ')
        x = CC[0] + int(data[0])
        y = CC[1] + int(data[1])
        size = int(data[2])
        color = data[3]
        try:
            pygame.draw.circle(screen, color, (x,y), size)
            if len(data) > 4:
                draw_text(x, y, size // 2, data[4],'black')
        except ValueError:
            print(x, y,size,color)

class Grid:
    def __init__(self, screen, color):
        self.screen = screen
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size
        self.color = color

    def update(self, parameters : list[int]):
        x, y, L = parameters
        self.size = self.start_size // L
        self.x = -self.size + (-x) % self.size
        self.y = -self.size + (-y) % self.size

    def draw(self):
        for i in range(WIDTH // self.size + 2):
            pygame.draw.line(self.screen, self.color, (self.x + i * self.size, 0), (self.x + i * self.size, HEIGHT),1)
        for i in range(HEIGHT // self.size + 2):
            pygame.draw.line(self.screen, self.color, (0, self.y + i * self.size), (WIDTH, self.y + i * self.size), 1)



name = ''
color = ''

root = tk.Tk()
root.title('Логин')
root.geometry('300x300')

style = ttk.Style()
style.theme_use('default')

name_label = tk.Label(root, text='Введите свой никнейм: ')
name_label.pack()
row = tk.Entry(root, width=40, justify="center")
row.pack()
color_label = tk.Label(root, text='Выбери цвет: ')
color_label.pack()
colors = ['Maroon', 'DarkRed', 'FireBrick', 'Red', 'Salmon', 'Tomato', 'Coral', 'OrangeRed', 'Chocolate', 'SandyBrown',
          'DarkOrange', 'Orange', 'DarkGoldenrod', 'Goldenrod', 'Gold', 'Olive', 'Yellow', 'YellowGreen', 'GreenYellow',
          'Chartreuse', 'LawnGreen', 'Green', 'Lime', 'SpringGreen', 'MediumSpringGreen', 'Turquoise',
          'LightSeaGreen', 'MediumTurquoise', 'Teal', 'DarkCyan', 'Aqua', 'Cyan', 'DeepSkyBlue',
          'DodgerBlue', 'RoyalBlue', 'Navy', 'DarkBlue', 'MediumBlue']
combo = ttk.Combobox(root, values=colors, textvariable=color)
combo.bind('<<ComboboxSelected>>', scroll)
combo.pack()
name_btn = tk.Button(root, text='Зайти в игру', command=login)
name_btn.pack()
root.mainloop()
window_size = 900,600 #Ввел размер фона
imgsky_image = pygame.image.load("imgsky.png")#загрузил скачанную картинку
imgsky_image  = pygame.transform.scale(imgsky_image, window_size)#отредактировал под размер окна

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.connect(('localhost', 10000))
sock.send(f'color:<{name},{color}>'.encode())
WIDTH = 800
HEIGHT = 600
radius = 50
CC = (WIDTH / 2, HEIGHT / 2)
old = (0, 0)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Бактерии")
pygame.init()
grid = Grid(screen, 'seashell4')

font = pygame.font.SysFont('Arial', 52)

def draw_text(x, y, r,  text, color ):
    font = pygame.font.Font(None, r)
    text = font.render(text, True, color)
    rect = text.get_rect(center = (x, y))
    screen.blit(text, rect)

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            vector = pos[0] - CC[0], pos[1] - CC[1]
            lenv = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
            vector = vector[0] / lenv, vector[1] / lenv
            if lenv < radius:
                vector = 0, 0
            if vector != old:
                old = vector
                msg = f'<{vector[0]},{vector[1]}>'
                sock.send(msg.encode())
    try:
        data = sock.recv(buffer).decode()
    except ConnectionAbortedError:
        run = False
        continue
    data = find(data).split(',')
    screen.fill('gray')
    if data != ['']:
        parameters = list(map(int, data[0].split(' ')))
        radius = parameters[0]
        grid.update(parameters[1:])
        grid.draw()
        draw_bakteries(data[1:])
    pygame.draw.circle(screen, color, CC, radius)
    draw_text(CC[0], CC[1], radius // 2, name, 'black')
    pygame.display.update()
# Изменения
screen.blit(imgsky_image, (0, 0))#
pygame.display.update()
pygame.display.flip()
game_over = font.render('Спасибо за игру!', 1, color)# создал текст и отредактировал
screen.blit(game_over, (150, 200))#вывел текст на экран
pygame.display.flip()
time.sleep(3)# установил время
pygame.quit()
