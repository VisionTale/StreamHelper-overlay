from requests import get

from webapi.libs.data_structures import inverse_stack


def backend_request(form: dict):
    from .. import config, name
    form.pop('csrf_token')
    method = None
    identifier = list(form.keys())[0].split('.')[0]

    if form.get(f'{identifier}.play'):
        form.pop(f'{identifier}.play')
        method = 'play_html'
    elif form.get(f'{identifier}.update'):
        form.pop(f'{identifier}.update')
        method = 'update_html'
    elif form.get(f'{identifier}.stop'):
        form.pop(f'{identifier}.stop')
        method = 'clear'
    if method:
        stack = inverse_stack(form, 'popitem')
        for i in range(len(stack)):
            stack[i] = (stack[i][0].split('.')[-1], stack[i][1])
        stack.append(('route', identifier))
        overlay_server = config.get(name, 'overlay_server')
        if not overlay_server.endswith('/'):
            overlay_server += '/'
        overlay_server += method
        if '://' not in overlay_server:
            overlay_server = 'http://' + overlay_server
        get(overlay_server, params=stack)
