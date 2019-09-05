#!/usr/bin/env python
import requests
import json

###### User Variables

username = 'admin'
password = 'Arista'
server1 = 'https://192.168.255.50'
builder_name = 'ImageDowngrade'
container_key = 'undefined_container'
downgrade_match = '4.22.1FX-CLI'

###### Do not modify anything below this line.
connect_timeout = 10
headers = {"Accept": "application/json",
           "Content-Type": "application/json"}
requests.packages.urllib3.disable_warnings()

session = requests.Session()

def login(url_prefix, username, password):
    authdata = {"userId": username, "password": password}
    headers.pop('APP_SESSION_ID', None)
    response = session.post(url_prefix+'/web/login/authenticate.do', data=json.dumps(authdata),
                            headers=headers, timeout=connect_timeout,
                            verify=False)
    cookies = response.cookies
    headers['APP_SESSION_ID'] = response.json()['sessionId']
    if response.json()['sessionId']:
        return response.json()['sessionId']

def logout(url_prefix):
    response = session.post(url_prefix+'/cvpservice/login/logout.do')
    return response.json()

def get_builder(url_prefix,builder_name):
    response = session.get(url_prefix+'/cvpservice/configlet/getConfigletByName.do?name='+builder_name)
    if response.json()['key']:
        return response.json()['key']

def run_builder(url_prefix,configlet_key,device_key):
    data = json.dumps({"previewValues":[],"configletBuilderId":configlet_key,"netElementIds":[device_key],"pageType":"","containerId":"","containerToId":"","mode":"preview"})
    response = session.post(url_prefix+'/cvpservice/configlet/configletBuilderPreview.do', data=data)
    return response.json()

def get_items_in_undefined(url_prefix):
    response = session.get(url_prefix+'/cvpservice/inventory/devices?provisioned=false')
    ztpDevices = []
    device_list = response.json()
    for device in device_list:
        if device['ztpMode'] == True and device['parentContainerKey'] == 'undefined_container' and device['version'] == downgrade_match:
            ztpDevices.append(device['systemMacAddress'])
    return ztpDevices

def main():
    device_list = []
    print '###### Logging into Server 1'
    login(server1, username, password)
    configlet_key = get_builder(server1,builder_name)
    ztpDevices = get_items_in_undefined(server1)
    for device_key in ztpDevices:
        output = run_builder(server1,configlet_key,device_key)
        print output
    logout(server1)
    print '##### Complete'

if __name__ == "__main__":
    main()
