import socket
from itertools import count

import psycopg2
import time
import math
import random

from pygame import font
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pygame
from russian_names import RussianNames

pygame.init()
WIDTH_ROOM, HEIGHT_ROOM = 4000, 4000
WIDTH_SERVER, HEIGHT_SERVER = 300, 300
FPS = 100
colors = ['Maroon', 'DarkRed', 'FireBrick', 'Red', 'Salmon', 'Tomato', 'Coral', 'OrangeRed', 'Chocolate', 'SandyBrown',
          'DarkOrange', 'Orange', 'DarkGoldenrod', 'Goldenrod', 'Gold', 'Olive', 'Yellow', 'YellowGreen', 'GreenYellow',
          'Chartreuse', 'LawnGreen', 'Green', 'Lime', 'SpringGreen', 'MediumSpringGreen', 'Turquoise',
          'LightSeaGreen', 'MediumTurquoise', 'Teal', 'DarkCyan', 'Aqua', 'Cyan', 'DeepSkyBlue',
          'DodgerBlue', 'RoyalBlue', 'Navy', 'DarkBlue', 'MediumBlue']
MOBS = 25
food_size = 15
food_quantity = HEIGHT_ROOM * WIDTH_ROOM // 40000
screen = pygame.display.set_mode((WIDTH_SERVER, HEIGHT_SERVER))
pygame.display.set_caption('Сервер')
clock = pygame.time.Clock()
clock.tick(FPS)

Base = declarative_base()
engine = create_engine('sqlite:///store.db')

Session = sessionmaker(bind=engine)
s = Session()
main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind(('localhost', 10000))
main_socket.setblocking(False)
main_socket.listen(5)
players = {}


def find_color(vector: str):
    first = vector.find('<')
    second = vector.find('>')
    if first < second or first >= 0:
        result = vector[first + 1:second]
        result = result.split(',')
        return result
    return ""


def find(vector: str):
    first = vector.find('<')
    second = vector.find('>')
    if first < second or first >= 0:
        result = vector[first + 1:second]
        result = result.split(',')
        result = list(map(float, result))
        return result
    return ""


class Player(Base):
    __tablename__ = 'gamers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250))
    address = Column(String(250))
    x = Column(Integer, default=500)
    y = Column(Integer, default=500)
    size = Column(Integer, default=50)
    errors = Column(Integer, default=0)
    abs_speed = Column(Integer, default=1)
    speed_x = Column(Integer, default=1)
    speed_y = Column(Integer, default=1)
    color = Column(String(250))
    w_vision = Column(Integer, default=800)
    h_vision = Column(Integer, default=600)

    def __init__(self, name, address):
        self.name = name
        self.address = address


Base.metadata.create_all(engine)


# Base.metadata.drop_all(engine)

class LocalPlayer:
    def __init__(self, name, id, address, sock):
        self.name = name
        self.sock = sock
        self.id = id
        self.db: Player = s.get(Player, self.id)
        self.address = address
        self.x = 500
        self.y = 500
        self.size = 50
        self.errors = 0
        self.abs_speed = 1
        self.speed_x = 0
        self.speed_y = 0
        self.color = 'red'
        self.w_vision = 800
        self.h_vision = 600
        self.L = 1

    def change_speed(self, vector):
        vector = find(vector)
        if vector[0] == 0 and vector[1] == 0:
            self.speed_x = self.speed_y = 0
        else:
            vector = vector[0] * self.abs_speed, vector[1] * self.abs_speed
            self.speed_x = vector[0]
            self.speed_y = vector[1]

    def update(self):
        if self.x - self.size <= 0:
            if self.speed_x >= 0:
                self.x += self.speed_x
        elif self.x + self.size >= WIDTH_ROOM:
            if self.speed_x <= 0:
                self.x += self.speed_x
        else:
            self.x += self.speed_x

        if self.y - self.size <= 0:
            if self.speed_y >= 0:
                self.y += self.speed_y
        elif self.y + self.size >= HEIGHT_ROOM:
            if self.speed_y <= 0:
                self.y += self.speed_y
        else:
            self.y += self.speed_y
        if self.size >= self.w_vision / 4:
            if self.w_vision <= WIDTH_ROOM or self.h_vision >= HEIGHT_ROOM:
                self.L *= 2
                self.w_vision = 800 * self.L
                self.h_vision = 600 * self.L
    def load(self):
        self.size = self.db.size
        self.errors = self.db.errors
        self.abs_speed = self.db.abs_speed
        self.speed_x = self.db.speed_x
        self.speed_y = self.db.speed_y
        self.color = self.db.color
        self.w_vision = self.db.w_vision
        self.h_vision = self.db.h_vision
        self.x = self.db.x
        self.y = self.db.y
        return self

    def sync(self):
        self.db.size = self.size
        self.db.errors = self.errors
        self.db.abs_speed = self.abs_speed
        self.db.speed_x = self.speed_x
        self.db.speed_y = self.speed_y
        self.db.color = self.color
        self.db.w_vision = self.w_vision
        self.db.h_vision = self.h_vision
        self.db.x = self.x
        self.db.y = self.y
        return self

    def new_speed(self):
        self.abs_speed = 10 / math.sqrt(self.size)

class Food():
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color


foods = []
for i in range(food_quantity):
    foods.append(Food(x=random.randint(0, WIDTH_ROOM), y=random.randint(0, HEIGHT_ROOM), size=food_size,
                      color=random.choice(colors)))

tick = -1
server_works = True

names = RussianNames(count=MOBS * 2, patronymic=False, surname=False, rare=True)
names = list(set(names))
for x in range(MOBS):
    server_mob = Player(names[x], None)
    server_mob.color = random.choice(colors)
    server_mob.x, server_mob.y = random.randint(0, WIDTH_ROOM), random.randint(0, HEIGHT_ROOM)
    server_mob.speed_x = random.randint(-1, 1)
    server_mob.speed_y = random.randint(-1, 1)
    server_mob.size = random.randint(10, 100)
    s.add(server_mob)
    s.commit()
    local_mob = LocalPlayer(server_mob.name, server_mob.id, None, None).load()
    players[server_mob.id] = local_mob

while server_works:
    clock.tick(FPS)
    tick += 1
    if tick % 200 == 0:
        try:
            new_socket, addr = main_socket.accept()
            new_socket.setblocking(False)
            print('Подключился', addr)
            new_socket.setblocking(False)
            login = new_socket.recv(1024).decode()
            addr = str(addr)
            player = Player('Имя', addr)

            if login.startswith('color'):
                data = find_color(login[6:])
                player.name, player.color = data

            s.merge(player)
            s.commit()
            data = s.query(Player).filter(Player.address == addr)
            for user in data:
                player = LocalPlayer(user.name, user.id, addr, new_socket).load()
                players[user.id] = player
        except BlockingIOError:
            pass
        need = MOBS - len(players)
        if need > 0:
            names = RussianNames(count=need * 2, patronymic=False, surname=False, rare=True)
            names = list(set(names))
            for x in range(need):
                server_mob = Player(names[x], None)
                server_mob.color = random.choice(colors)
                spawn: Food = random.choice(foods)
                server_mob.x, server_mob.y = spawn.x, spawn.y
                server_mob.size = random.randint(10, 100)
                server_mob.speed_x = random.randint(-1, 1)
                server_mob.speed_y = random.randint(-1, 1)
                s.add(server_mob)
                s.commit()
                local_mob = LocalPlayer(server_mob.name, server_mob.id, None, None).load()
                local_mob.new_speed()
                players[server_mob.id] = local_mob
        need = food_quantity - len(foods)
        for i in range(need):
            foods.append(Food(x=random.randint(0, WIDTH_ROOM), y=random.randint(0, HEIGHT_ROOM), size = food_size, color=random.choice(colors)))
    for id in list(players):
        if players[id].sock is not None:
            try:
                data = players[id].sock.recv(1024).decode()
                print('Получил', data)
                players[id].change_speed(data)
            except:
                pass
        else:
            if tick % 400 == 0:
                vector = f'<{random.randint(-1, 1)} , {random.randint(-1, 1)}>'
                players[id].change_speed(vector)
    visible_bacteries = {}
    for id in list(players):
        visible_bacteries[id] = []

    pairs = list(players.items())
    for i in range(0, len(pairs)):
        for food in foods:
            hero: LocalPlayer = pairs[i][1]
            dist_x = food.x - hero.x
            dist_y = food.y - hero.y
            if abs(dist_x) <= hero.w_vision // 2 + food.size and abs(dist_y) <= hero.h_vision // 2 + food.size:

                distance = math.sqrt(dist_x ** 2 + dist_y ** 2)
                if distance < hero.size:
                    hero.size = math.sqrt(hero.size ** 2 + food.size ** 2)
                    hero.new_speed()
                    food.size = 0
                    foods.remove(food)
                if hero.address is not None and food_size != 0:
                    x_ = str(round(dist_x / hero.L))
                    y_ = str(round(dist_y / hero.L))
                    size_ = str(round(food.size / hero.L))
                    color_ = food.color
                    data = x_ + ' ' + y_ + ' ' + size_ + ' ' + color_
                    visible_bacteries[hero.id].append(data)
        for j in range(i + 1, len(pairs)):
            hero1: LocalPlayer = pairs[i][1]
            hero2: LocalPlayer = pairs[j][1]
            dist_x = hero2.x - hero1.x
            dist_y = hero2.y - hero1.y
            if abs(dist_x) <= hero1.w_vision // 2 + hero2.size and abs(dist_y) <= hero1.h_vision // 2 + hero2.size:

                distance = math.sqrt(dist_x ** 2 + dist_y ** 2)
                if distance <= hero1.size and hero1.size > 1.1 * hero2.size:
                    hero1.size = math.sqrt(hero1.size ** 2 + hero2.size ** 2)
                    hero1.new_speed()
                    hero2.size, hero2.speed_x, hero2.speed_y = 0, 0, 0
                if hero1.address is not None:
                    print(1)
                    x_ = str(round(dist_x / hero1.L))
                    y_ = str(round(dist_y / hero1.L))
                    size_ = str(round(hero2.size / hero1.L))
                    color_ = hero2.color
                    name_ = hero2.name
                    data = x_ + ' ' + y_ + ' ' + size_ + ' ' + color_
                    if hero2.size >= 30 * hero1.L:
                        data += ' ' + name_
                    visible_bacteries[hero1.id].append(data)
            if abs(dist_x) <= hero2.w_vision // 2 + hero1.size and abs(dist_y) <= hero2.h_vision // 2 + hero1.size:
                distance = math.sqrt(dist_x ** 2 + dist_y ** 2)
                if distance <= hero2.size and hero2.size > 1.1 * hero1.size:
                    hero2.size = math.sqrt(hero2.size ** 2 + hero1.size ** 2)
                    hero2.new_speed()
                    hero1.size, hero1.speed_x, hero1.speed_y = 0, 0, 0
                if hero2.address is not None:
                    x_ = str(round(-dist_x / hero2.L))
                    y_ = str(round(-dist_y / hero2.L))
                    size_ = str(round(hero1.size / hero2.L))
                    color_ = hero1.color
                    name_ = hero1.name
                    data = x_ + ' ' + y_ + ' ' + size_ + ' ' + color_
                    if hero1.size >= 30 * hero2.L:
                        data += ' ' + name_
                    visible_bacteries[hero2.id].append(data)
    for id in list(players):
        r_ = str(round(players[id].size  / players[id].L))
        x_ = str(round(players[id].x / players[id].L))
        y_ = str(round(players[id].y / players[id].L))
        L_ = str(round(players[id].L))
        visible_bacteries[id] = [r_ + ' ' + x_ + ' ' + y_ + ' ' + L_] + visible_bacteries[id]
        visible_bacteries[id] = '<' + ','.join(visible_bacteries[id]) + '>'
    for id in list(players):
        if players[id].sock is not None:
            try:
                players[id].sock.send(visible_bacteries[id].encode())
            except:
                players[id].sock.close()
                del players[id]
                s.query(Player).filter(Player.id == id).delete()
                s.commit()
                print("Сокет закрыт")
    for id in list(players):
        if players[id].errors >= 500 or players[id].size == 0:
            if players[id].sock is not None:
                players[id].sock.close()
            del players[id]
            s.query(Player).filter(Player.id == id).delete()
            s.commit()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            server_works = False
    screen.fill('black')
    for id in players:
        player = players[id]
        x = player.x * WIDTH_SERVER // WIDTH_ROOM
        y = player.y * HEIGHT_SERVER // HEIGHT_ROOM
        size = player.size * WIDTH_SERVER // WIDTH_ROOM
        pygame.draw.circle(screen, player.color, (x, y), size)
    for id in list(players):
        player = players[id]
        player.update()
    pygame.display.update()
pygame.quit()
main_socket.close()
s.query(Player).delete()
s.commit()
