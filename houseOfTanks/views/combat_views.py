from django.shortcuts import render, redirect
from django.views.generic import TemplateView
import json
import configparser
import stomp
import random


def get_config():
    config = configparser.ConfigParser()
    config.read("static/config/config.ini")
    return config


# Config
config = get_config()


class Tank:

    def __init__(self):
        # self.move = 3

        self.weapon_selected = ""
        self.pv = 1000
        self.shield = 0
        self.power = ""
        self.money = 5000
        self.location = [0, 0]

        with open("static/weapon.json", 'r+') as file:
            data_as_string = file.read()
            self.weapon_list = json.loads(data_as_string)
            file.close()

    def choice_weapon(self, weapon_name):
        for weapon in self.weapon_list:
            if weapon['nom'] == weapon_name:
                self.weapon_selected = weapon.copy()
                break


class IndexView(TemplateView):
    template_name = 'combat.html'
    tank = Tank()

    def get(self, request, *args, **kwargs):

        # Variables
        username = request.COOKIES.get('username')
        broker_host = request.COOKIES.get('ip')
        move = request.GET.get('move')
        broker_port = config["BROKER"]["PORT"]
        print('broker_host :', broker_host, 'broker_port :', broker_port)


        # Move
        if move:
            # Connection
            broker = stomp.Connection([(broker_host, broker_port)], heartbeats=(30000, 30000))
            broker.connect(config["BROKER"]["USERNAME"], config["BROKER"]["PASSWORD"], wait=True)
            message = None
            if move == "up":
                message = {"direction": "FORWARD"}
            elif move == "left":
                message = {"direction": "LEFT"}
            elif move == "right":
                message = {"direction": "RIGHT"}
            elif move == "down":
                message = {"direction": "BACKWARD"}
            elif move == "stop":
                message = {"direction": "NONE"}

            broker.send(destination=config["BROKER"]["MOTOR_LISTEN_TOPIC"],
                        headers={"type": config["MOTOR"]["MESSAGE_TYPE_DIRECTION"]},
                        body=json.dumps(message))
            broker.disconnect()

            """if move == "up":
                self.tank.location[1] += 1
                print(self.tank.location)
            elif move == "left":
                self.tank.location[0] -= 1
                print(self.tank.location)
            elif move == "right":
                self.tank.location[0] += 1
                print(self.tank.location)
            elif move == "down":
                self.tank.location[1] -= 1
                print(self.tank.location)"""

        context = {
            "username": username,
            "ip": broker_host,
            "tank": self.tank,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        price = request.POST.get('price')
        weapon_name = request.POST.get('nom')
        shot = request.POST.get('shot')

        response = redirect("/combat")

        # --> Achat
        if price:
            if int(self.tank.money) >= int(price):
                self.tank.money -= int(price)
                self.tank.choice_weapon(weapon_name)
                print('Weapon : ', self.tank.weapon_selected)
            else:
                print("Vous n'avez pas assez d'argent")

        if shot:
            shooting_chance = random.randint(0, 100)
            if shooting_chance > 80:
                print('Shot missed')
            elif shooting_chance <= 80:
                print('Shot successful')

        response.set_cookie("argent", self.tank.money)

        return response
