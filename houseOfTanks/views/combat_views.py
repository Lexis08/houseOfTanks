from django.shortcuts import render
from django.views.generic import TemplateView
import json


class Tank:

    def __init__(self):
        self.move = 3
        self.weapon = ""
        self.pv = 1000
        self.shield = 500
        self.power = ""

        with open("weapon.json", 'r+') as file:
            data_as_string = file.read()
            self.weapon_list = json.loads(data_as_string)
            file.close()

    def choice_weapon(self, weapon_name):
        self.weapon = self.weapon_list[weapon_name]


class IndexView(TemplateView):
    template_name = 'combat.html'

    def get(self, request, *args, **kwargs):

        username = request.COOKIES.get('username')
        ip = request.COOKIES.get('ip')

        tank = Tank()

        context = {
            "username": username,
            "ip": ip,
            "weapon_list": tank.weapon_list,
        }
        return render(request, self.template_name, context)
