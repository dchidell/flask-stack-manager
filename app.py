from flask import Flask, request, jsonify, redirect, url_for
from jinja2 import Environment, FileSystemLoader
import docker
import time
import json

__author__ = 'David Chidell (dchidell@cisco.com)'

app = Flask(__name__)

GLOBAL_FILE = 'global.conf'
global_data = {}

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
    global global_data
    client = docker.from_env()
    container = client.containers.get(container)
    return_data = jsonify({'success':True})
    if operation == 'start':
        container.start()
    elif operation == 'stop':
        container.kill()
    elif operation == 'clearlogs':
        global_data[container.attrs['Id']+'_logs'] = int(time.time())
        write_global()
    elif operation == 'logs':
        read_global()
        log_stamp = global_data.get(container.attrs['Id']+'_logs',None)
        if log_stamp is not None:
            return_data = container.logs(since=log_stamp).decode().replace('\n','<br>')
        else:
            return_data = container.logs().decode().replace('\n','<br>')

    redirect_path = request.args.get('redir',None)

    if redirect_path is None:
        return return_data
    elif redirect_path == 'home':
        return redirect(url_for('index'))
    else:
        return redirect(redirect_path)

def read_global():
    global global_data
    try:
        with open(GLOBAL_FILE,'r') as f:
            d = json.loads(f.read())
        d.update(global_data)
        global_data = d
    except FileNotFoundError:
        pass
    finally: 
        return global_data


def write_global():
    global global_data
    read_global()
    with open(GLOBAL_FILE,'w') as f:
        f.write(json.dumps(global_data))

if __name__ == '__main__':
    app.run()

