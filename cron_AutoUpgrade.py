#!/usr/bin/env python
import requests
import json

###### User Variables

username = 'admin'
password = 'Arista123'
server1 = 'https://192.168.255.50'
builder_name = 'builder_AutoUpgrade.py'
container_key = 'undefined_container'
undefinedContainerName = 'Undefined'

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

def rest_getBundleApplied(url_prefix,imageNames):
    rest_getAssignedBundle = '/cvpservice/image/getImageBundleAppliedContainers.do?startIndex=0&endIndex=0&imageName='
    for imageBundle in imageNames:
        response = session.get(url_prefix+rest_getAssignedBundle+imageNames[imageBundle]+'&queryparam='+undefinedContainerName)
        # Parses configlet data into JSON.
        imageBundles = response.json()
        if imageBundles['total'] == 1:
            return imageBundle

def get_undefined_image(url_prefix):
    imageNames = {}
    rest_getImageBundles = '/cvpservice/image/getImageBundles.do?startIndex=0&endIndex=0'
    client = session.get(url_prefix+rest_getImageBundles)
    # Parses configlet data into JSON.
    imageBundles = client.json()['data']
    for image in imageBundles:
        imageNames.update({image['key']:image['name']})
    undefinedVersion = rest_getBundleApplied(url_prefix,imageNames)
    for image in imageBundles:
        if image['key'] == undefinedVersion:
            imageList = image['imageIds']
    for image in imageList:
        if image.lower().endswith('.swi'):
            finalImage = image
    return finalImage

def get_items_in_undefined(url_prefix):
    response = session.get(url_prefix+'/cvpservice/inventory/devices?provisioned=false')
    ztpDevices = []
    device_list = response.json()
    undefinedImage = get_undefined_image(server1)
    for device in device_list:
        deviceVersion = int(device['version'].split('.')[1])
        upgradeVersion = int(undefinedImage.split('.')[1])
        if device['ztpMode'] == True and device['parentContainerKey'] == 'undefined_container' and deviceVersion <= upgradeVersion and device['streamingStatus'] == 'active':
            ztpDevices.append(device['systemMacAddress'])
    return ztpDevices

def main():
    device_list = []
    print '###### Logging into Server 1'
    login(server1, username, password)
    configlet_key = get_builder(server1,builder_name)
    ztpDevices = get_items_in_undefined(server1)
    for device_key in ztpDevices:
        try:
            output = run_builder(server1,configlet_key,device_key)
            print output
        except:
            pass
    logout(server1)
    print '##### Complete'

if __name__ == "__main__":
    main()
