from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class LogView(TemplateView):
    template_name = 'log.html'

    def get(self, request, *args, **kwargs):

        context = {}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):

        # Parametre
        username = request.POST.get('username')
        ip_adress = request.POST.get('ip_adress')
        tid = request.POST.get('tid')

        # response = HttpResponse('hello')
        response = redirect("/combat")
        response.set_cookie("username", username)
        response.set_cookie("ip", ip_adress)
        response.set_cookie("tid", tid)

        return response

