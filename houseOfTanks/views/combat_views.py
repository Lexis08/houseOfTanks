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
    # print("===> move")
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
    # print("===> stop")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    message = {"direction": "NONE"}
    tank.broker.send(destination=config["BROKER"]["MOTOR_LISTEN_TOPIC"],
                headers={"type": config["MOTOR"]["MESSAGE_TYPE_DIRECTION"]},
                body=json.dumps(message))
    return JsonResponse({"result": "ok"})

def connection(request):
    # Connection
    print('===> connection')
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    tank.broker = stomp.Connection([(tank.ip_adress, tank.broker_port)], heartbeats=(30000, 30000))
    tank.broker.connect(config["BROKER"]["USERNAME"], config["BROKER"]["PASSWORD"], wait=True)

    # Subscribe
    tank.broker.set_listener('broker_listener', SimpleConnectionListener(tank.broker))
    tank.broker.subscribe("/queue/camera/action_response", 'hot_camera_subscriber')

    print('===> connection started')

    return JsonResponse({"txt": "Connection started"})

def shot_detection_request(request):
    print("===> Shot detection request")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    if tank.weapon_selected:
        print('--> Envoie du message')
        msg = 'Envoie du message'
        message = {"none": "none"}
        tank.broker.send(destination="/queue/camera/action_request",
                    headers={"type": "SHOOT"},
                    body=json.dumps(message))
        #FIXME a supprimer
        # shot_detection_response(None, None)
    else:
        print('--> Choice a weapon')
        msg = 'Choice a weapon'
    #TODO envoyer le message
    return JsonResponse({"msg": msg})

#TODO Buy by Ajax
def buy_weapon(request):
    print("===> buy_weapon")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    price_weapon = request.GET.get('price_weapon')
    weapon_name = request.GET.get('weapon_name')
    if int(tank.money) >= int(price_weapon):
        tank.money -= int(price_weapon)
        tank.weapon_selected = tank.choice_item(tank.weapon_list, weapon_name)
        print("--> Achat effectué")
        msg = "Achat effectué"
    else:
        print("--> Vous n'avez pas assez d'argent")
        msg = "Vous n'avez pas assez d'argent"
    #TODO afficher le message
    return JsonResponse({"msg": msg})

def buy_shield(request):
    print("===> buy_shield")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    price_shield = request.GET.get('price_shield')
    shield_name = request.GET.get('shield_name')
    if int(tank.money) >= int(price_shield):
        tank.money -= int(price_shield)
        tank.shield_selected = tank.choice_item(tank.shield_list, shield_name)
        print("--> Achat effectué")
        msg = "Achat effectué"
    else:
        print("--> Vous n'avez pas assez d'argent")
        msg = "Vous n'avez pas assez d'argent"
    #TODO afficher le message
    return JsonResponse({"msg": msg})

#################################################
# BROKER LISTENER
#################################################
class SimpleConnectionListener(stomp.ConnectionListener):
    def __init__(self, connection):
        self.conn = connection

    def on_message(self, frame):
        print("Receive message : type = [{}], message = [{}]".format(frame.headers.get('type', None), frame.body))
        if frame.headers.get('type', None) == 'action_response':
            shot_detection_response(frame.headers, frame.body)
        elif frame.headers.get('type', None) == 'IMAGE':
            print(f"received image")
        else:
            print(f"unknown message type ... no callback")

# class SimpleConnectionListener(stomp.ConnectionListener):
#     def __init__(self, connection, callback):
#         self.conn = connection
#         self.callback = callback
#
#     def on_message(self, frame):
#         print("Receive message : type = [{}], message = [{}]".format(frame.headers.get('type', None), frame.body))
#         self.callback(frame.headers, frame.body)

#################################################
# WEBSOCKET
#################################################
import requests

def save_websocket_sid(request):
    print("===> save_websocket_sid")
    tank = tid_to_tank_dict[request.COOKIES.get('tid')]
    tank.sid = request.COOKIES.get('websocket_sid')
    # print(f"SID : {tank.sid}")
    return JsonResponse({"result": "ok"})

def shot_detection_response(headers, body): # Quand broker envoit une reponse

    # response = {
    #     "action": 'SHOOT',
    #     "src_tid": 1,
    #     "target_tid": '',
    #     "face": 0
    # }

    response = json.loads(body)

    print("===> Receive shot tag result")
    tank = tid_to_tank_dict[str(response['src_tid'])]

    # Verifie si il voit un tank su lequel tirer
    if response['target_tid']:
        target_tank = tid_to_tank_dict[str(response['target_tid'])]
        # Tir
        shooting_chance = random.randint(0, 100)
        if shooting_chance > tank.weapon_selected['precision']:
            data = {
                'src_sid': tank.sid,
                'src_msg': 'Shot missed',
                'src_pv': tank.pv,
                'src_shield': tank.shield,
                'target_sid': '',
                'target_msg': '',
                'target_pv': '',
                'target_shield': ''
            }
        else:
            target_tank.shield -= tank.weapon_selected['degats']
            if target_tank.shield < 0:
                target_tank.pv += target_tank.shield
                target_tank.shield = 0
            data = {
                'src_sid': tank.sid,
                'src_msg': 'Shot successful',
                'src_pv': tank.pv,
                'src_shield': tank.shield,
                'target_sid': target_tank.sid,
                'target_msg': f'Degats : {tank.weapon_selected['degats']}',
                'target_pv': target_tank.pv,
                'target_shield': target_tank.shield
            }

    else:
        data = {
            'src_sid': tank.sid,
            'src_msg': 'No tank',
            'src_pv': tank.pv,
            'src_shield': tank.shield,
            'target_sid': '',
            'target_msg': '',
            'target_pv': '',
            'target_shield': ''
        }

    requests.post('http://192.168.1.45:3000/dispatch_shoot_result', json=data)

#################################################

def get_config():
    config_ = configparser.ConfigParser()
    config_.read("static/config/config.ini")
    return config_

# Config
config = get_config()


class Tank:

    def __init__(self):
        # User
        self.username = None
        self.ip_adress = None
        self.tid = None
        self.broker = None
        self.broker_port = None
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

    def get(self, request, *args, **kwargs):
        tid = request.COOKIES.get('tid')

        if tid not in tid_to_tank_dict:
            tank = Tank()

            # Variables
            tank.username = request.COOKIES.get('username')
            tank.ip_adress = request.COOKIES.get('ip_adress')
            tank.tid = request.COOKIES.get('tid')

            # Ajout du tank au dict
            tid_to_tank_dict[tank.tid] = tank

            # Broker Port
            tank.broker_port = config["BROKER"]["PORT"]

        else:
            tank = tid_to_tank_dict[tid]

            # Variables
            tank.username = request.COOKIES.get('username')
            tank.ip_adress = request.COOKIES.get('ip_adress')
            tank.tid = request.COOKIES.get('tid')

        context = {
            "tank": tank,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        tank = tid_to_tank_dict[request.COOKIES.get('tid')]

        # Parameters
        price_weapon = request.POST.get('price_weapon')
        price_shield = request.POST.get('price_shield')
        weapon_name = request.POST.get('weapon_nom')
        shield_name = request.POST.get('shield_nom')

        response = redirect("/combat")

        # --> Achat arme
        if price_weapon:
            if int(tank.money) >= int(price_weapon):
                tank.money -= int(price_weapon)
                tank.weapon_selected = tank.choice_item(tank.weapon_list, weapon_name)
            else:
                print("--> Vous n'avez pas assez d'argent")
        # --> Achat shield
        if price_shield:
            if int(tank.money) >= int(price_shield):
                tank.money -= int(price_shield)
                tank.shield_selected = tank.choice_item(tank.shield_list, shield_name)
                tank.shield += tank.shield_selected['valeur']
            else:
                print("--> Vous n'avez pas assez d'argent")

        response.set_cookie("argent", tank.money)

        return response
