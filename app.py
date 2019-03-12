from flask import Flask, request, jsonify, redirect, url_for
from jinja2 import Environment, FileSystemLoader
import docker
import time

__author__ = 'David Chidell (dchidell@cisco.com)'

app = Flask(__name__)

log_dates = {}

@app.route('/')
def index():
    client = docker.from_env()
    output_list = [] 

    for container in client.containers.list(all=True,filters={'label':'traefik.frontend.rule'}):
        rule = container.labels.get('traefik.frontend.rule',None)
        if rule is None or 'catchall' in rule: continue
        
        output_list.append(container.attrs)

    env = Environment(loader = FileSystemLoader('.'))
    template = env.get_template('main.html')
    return template.render(config=output_list,hostname=client.info()['Name'])

@app.route('/api/operate/<operation>/<container>',methods=['GET'])
def operate(operation,container):
    client = docker.from_env()
    container = client.containers.get(container)
    return_data = jsonify({'success':True})
    if operation == 'start':
        container.start()
    elif operation == 'stop':
        container.kill()
    elif operation == 'clearlogs':
        log_dates[container['Id']] = int(time.time())
    elif operation == 'logs':
        if log_dates.get(container['Id'],None) is not None:
            return_data = container.logs(since=log_dates.get(container['Id'],None)).decode().replace('\n','<br>')
        else:
            return_data = container.logs().decode().replace('\n','<br>')

    redirect_path = request.args.get('redir',None)

    if redirect_path is None:
        return return_data
    elif redirect_path == 'home':
        return redirect(url_for('index'))
    else:
        return redirect(redirect_path)

#@app.errorhandler(Exception)
#def unhandled_exception(e):
#    return str(e)

'''
@app.route('/api/info/<name>',methods=['GET'])
def logs(name):
    client = docker.from_env()


    try:
        

    

    
    json_dict = request.json
    if type(json_dict) is not dict:
        response['exception'] = 'Unable to parse JSON. Ensure Content-Type is set correctly and payload is valid JSON.'
    else:
        try:
            module = importlib.import_module(name)
            output = module.invoke(json_dict).execute()
            response['output'] = output
            response['success'] = True
        except Exception as e:
            response['exception'] = str(e)
        finally:
            del module

    return jsonify(response)
'''
if __name__ == '__main__':
    app.run()

