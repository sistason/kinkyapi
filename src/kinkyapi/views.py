from django.shortcuts import render_to_response
from django.template import RequestContext


def index(request):
    return_dict = {'apis': [{'name': 'Kink.com', 'url': '/kinkcom'}]}

    return render_to_response('index.html', return_dict, RequestContext(request))
