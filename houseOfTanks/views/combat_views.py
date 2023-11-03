from django.shortcuts import render, redirect
from django.views.generic import TemplateView
import json
import configparser
import stomp
import random

tid_to_tank_dict = {}

#################################################
# AJAX
#################################################
from django.http import JsonResponse
def move(request):
    print("===> move")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    direction = request.GET.get('move')
    message = None
    if direction == "up":
        message = {"direction": "FORWARD"}
    elif direction == "left":
        message = {"direction": "LEFT"}
    elif direction == "right":
        message = {"direction": "RIGHT"}
    elif direction == "down":
        message = {"direction": "BACKWARD"}

    tank.broker.send(destination=config["BROKER"]["MOTOR_LISTEN_TOPIC"],
                headers={"type": config["MOTOR"]["MESSAGE_TYPE_DIRECTION"]},
                body=json.dumps(message))
    return JsonResponse({"result": "ok"})

def stop(request):
    print("===> stop")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    message = {"direction": "NONE"}
    tank.broker.send(destination=config["BROKER"]["MOTOR_LISTEN_TOPIC"],
                headers={"type": config["MOTOR"]["MESSAGE_TYPE_DIRECTION"]},
                body=json.dumps(message))
    return JsonResponse({"result": "ok"})

def buy_weapon(request):
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    price_weapon = request.GET.get('price_weapon')
    weapon_name = request.GET.get('weapon_name')
    if int(tank.money) >= int(price_weapon):
        tank.money -= int(price_weapon)
        tank.weapon_selected = tank.choice_item(tank.weapon_list, weapon_name)
        print('Weapon :', tank.weapon_selected)
    else:
        print("Vous n'avez pas assez d'argent")

def buy_shield(request):
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    price_shield = request.GET.get('price_shield')
    shield_name = request.GET.get('shield_name')
    if int(tank.money) >= int(price_shield):
        tank.money -= int(price_shield)
        tank.shield_selected = tank.choice_item(tank.shield_list, shield_name)
        print('Shield :', tank.shield_selected)
    else:
        print("Vous n'avez pas assez d'argent")

#################################################
# WEBSOCKET
#################################################
import requests

def save_websocket_sid(request):
    print("===> save_websocket_sid")

    # print(type(request.COOKIES.get('tid')))
    print(tid_to_tank_dict)

    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    tank.sid = request.COOKIES.get('websocket_sid')
    print(f"SID : {tank.sid}")
    return JsonResponse({"result": "ok"})

def shot_detection_request(request):
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    if tank.weapon_selected:
        #TODO envoyer un message "tag" sur le broker
        print("===> Marker detection request")
        #FIXME a supprimer
        shot_detection_response(request)
    else:
        print('===> Choice a weapon')
    return JsonResponse({"result": "ok"})

#TODO si reponse broker
def shot_detection_response(response_broker): # Quand broker envoit une reponse

    response = {
        "action": 'SHOOT',
        "src_tid": 2,
        "target_tid": 1,
        "face": 0
    }

    print("===> Receive tag result")
    print(tid_to_tank_dict)
    tank = tid_to_tank_dict[str(response['src_tid'])]

    # Verifie si target
    if response['target_tid']:
        target_tank = tid_to_tank_dict[str(response['target_tid'])]
        # Tir
        shooting_chance = random.randint(0, 100)
        if shooting_chance > tank.weapon_selected['precision']:
            print('Shot missed')
            data = {
                'src_sid': tank.sid,
                'target_sid': '',
                'src_msg': 'Shot missed'
            }
        else:
            print('Shot successful')
            data = {
                'src_sid': tank.sid,
                'target_sid': target_tank.sid,
                'src_msg': 'Shot successful',
                'target_msg': '-30'
            }
    else:
        data = {
            'src_sid': tank.sid,
            'target_sid': '',
            'src_msg': 'No tank'
        }

    requests.post('http://127.0.0.1:3000/dispatch_shoot_result', json=data)

#################################################

def get_config():
    config = configparser.ConfigParser()
    config.read("static/config/config.ini")
    return config


# Config
config = get_config()


class Tank:

    def __init__(self):
        # User
        self.username = None
        self.ip_adress = None
        self.tid = None
        self.broker = None
        self.sid = None
        # Ojet Tank
        self.weapon_selected = None
        self.shield_selected = None
        self.pv = 1000
        self.shield = 0
        self.power = None
        self.money = 5000
        self.location = [0, 0]

        with open("static/weapon.json", 'r+') as file:
            data_as_string = file.read()
            self.weapon_list = json.loads(data_as_string)
            file.close()

        with open("static/shield.json", 'r+') as file:
            data_as_string = file.read()
            self.shield_list = json.loads(data_as_string)
            file.close()

    def choice_item(self, item_list, item_name):
        for item in item_list:
            if item['nom'] == item_name:
                return item.copy()


class IndexView(TemplateView):
    template_name = 'combat.html'
    tank = Tank()

    def get(self, request, *args, **kwargs):

        # Ajout du tank au dict
        tid_to_tank_dict[self.tank.tid] = self.tank

        # Variables
        self.tank.username = request.COOKIES.get('username')
        self.tank.ip_adress = request.COOKIES.get('ip_adress')
        self.tank.tid = request.COOKIES.get('tid')
        broker_port = config["BROKER"]["PORT"]
        print('broker_host :', self.tank.ip_adress, 'broker_port :', broker_port)

        # Connection
        # self.tank.broker = stomp.Connection([(self.tank.ip_adress, broker_port)], heartbeats=(30000, 30000))
        # self.tank.broker.connect(config["BROKER"]["USERNAME"], config["BROKER"]["PASSWORD"], wait=True)

        context = {
            "tank": self.tank,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        # Parameters
        price_weapon = request.POST.get('price_weapon')
        price_shield = request.POST.get('price_shield')
        weapon_name = request.POST.get('weapon_nom')
        shield_name = request.POST.get('shield_nom')

        response = redirect("/combat")

        # --> Achat arme
        if price_weapon:
            if int(self.tank.money) >= int(price_weapon):
                self.tank.money -= int(price_weapon)
                self.tank.weapon_selected = self.tank.choice_item(self.tank.weapon_list, weapon_name)
                print('Weapon :', self.tank.weapon_selected)
            else:
                print("Vous n'avez pas assez d'argent")
        # --> Achat shield
        if price_shield:
            if int(self.tank.money) >= int(price_shield):
                self.tank.money -= int(price_shield)
                self.tank.shield_selected = self.tank.choice_item(self.tank.shield_list, shield_name)
                print('Shield :', self.tank.shield_selected)
            else:
                print("Vous n'avez pas assez d'argent")

        response.set_cookie("argent", self.tank.money)

        return response
