from django.shortcuts import render, redirect
from django.views.generic import TemplateView
import json
import sys
import configparser
import stomp


def get_config():
    config = configparser.ConfigParser()
    config.read("static/config/config.ini")
    return config


# Config
config = get_config()


class Tank:

    def __init__(self):
        self.move = 3
        self.weapon_selected = ""
        self.pv = 1000
        self.shield = 500
        self.power = ""
        self.argent = 5000

        with open("static/weapon.json", 'r+') as file:
            data_as_string = file.read()
            self.weapon_list = json.loads(data_as_string)
            file.close()

    def choice_weapon(self, weapon_name):
        for weapon in self.weapon_list:
            if weapon['nom'] == weapon_name:
                self.weapon_selected = weapon


class IndexView(TemplateView):
    template_name = 'combat.html'
    tank = Tank()

    def get(self, request, *args, **kwargs):

        # Variables
        username = request.COOKIES.get('username')
        broker_host = request.COOKIES.get('ip')
        move = request.GET.get('move')
        broker_port = config["BROKER"]["PORT"]
        print(broker_host, '', broker_port)

        # Connection
        broker = stomp.Connection([(broker_host, broker_port)], heartbeats=(30000, 30000))
        broker.connect(config["BROKER"]["USERNAME"], config["BROKER"]["PASSWORD"], wait=True)

        # Move
        if move:
            message = None
            if move == "up":
                message = {"direction": "FORWARD"}
            elif move == "left":
                message = {"direction": "FORWARD"}
            elif move == "right":
                message = {"direction": "FORWARD"}
            elif move == "down":
                message = {"direction": "FORWARD"}
            elif move == "stop":
                message = {"direction": "NONE"}

            broker.send(destination=config["BROKER"]["MOTOR_LISTEN_QUEUE"],
                        headers={"type": config["MOTOR"]["MESSAGE_TYPE_DIRECTION"]},
                        body=json.dumps(message))

        broker.disconnect()

        context = {
            "username": username,
            "ip": broker_host,
            "tank": self.tank,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        price = request.POST.get('price')
        weapon_name = request.POST.get('nom')

        response = redirect("/combat")

        # --> Achat
        if price:
            if int(self.tank.argent) >= int(price):
                self.tank.argent -= int(price)
                self.tank.choice_weapon(weapon_name)
                print('Weapon : ', self.tank.weapon_selected)
            else:
                print("Vous n'avez pas assez d'argent")

        response.set_cookie("argent", self.tank.argent)

        return response
