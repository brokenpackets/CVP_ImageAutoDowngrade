from cvplibrary import CVPGlobalVariables, GlobalVariableNames, Device, RestClient
import json
import ssl
import os

# Ignore untrusted/self-signed certificates.
ssl._create_default_https_context = ssl._create_unverified_context

# Stage device image with gold standard.
# Uses the image bundle applied to the Undefined container, but can be manually configured for a specific image.

#### User Vars
cvp_image = 'undefined' # 'undefined' or 'specific'
specific_image = 'EOS-4.21.7.1M.swi' #only used if cvp_image is flagged as 'specific'
image_to_downgrade = '4.22.1FX-CLI' # image to match against for processing Downgrades.
undefinedContainerName = 'Undefined' # modify this if user has renamed the Undefined container.

#### System Vars
cvpIP = os.environ.get('PRIMARY_DEVICE_INTF_IP', None)
cvpserver = 'https://localhost:443'
cvpserverIP = 'https://'+cvpIP
cvpDownloadPath = cvpserverIP+'/cvpservice/image/getImagebyId/'
cvpInstallImage = 'install source '+cvpDownloadPath
rest_getImageBundles = '/cvpservice/image/getImageBundles.do?startIndex=0&endIndex=0'
rest_getAssignedBundle = '/cvpservice/image/getImageBundleAppliedContainers.do?startIndex=0&endIndex=0&imageName='
#### Script Logic

def get_bundle_swi(bundleKey):
    pass

def get_undefined_image():
    imageNames = {}
    client = RestClient(cvpserver+rest_getImageBundles,'GET')
    if client.connect():
        # Parses configlet data into JSON.
        imageBundles = json.loads(client.getResponse())['data']
        for image in imageBundles:
            imageNames.update({image['key']:image['name']})
        undefinedVersion = rest_getBundleApplied(imageNames)
        for image in imageBundles:
            if image['key'] == undefinedVersion:
                imageList = image['imageIds']
        for image in imageList:
            if image.lower().endswith('.swi'):
                finalImage = image
    return finalImage

def rest_getBundleApplied(imageNames):
        for imageBundle in imageNames:
            client = RestClient(cvpserver+rest_getAssignedBundle+imageNames[imageBundle]+'&queryparam='+undefinedContainerName,'GET')
            if client.connect():
                # Parses configlet data into JSON.
                imageBundles = json.loads(client.getResponse())
                if imageBundles['total'] == 1:
                    return imageBundle

def main():
    if CVPGlobalVariables.getValue(GlobalVariableNames.ZTP_STATE) == 'true': # If device in ztp state, continue.
        device_ip = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_IP) # Get Device IP
        device_user = CVPGlobalVariables.getValue(GlobalVariableNames.ZTP_USERNAME) # Get CVP temp username for ZTP.
        device_pass =CVPGlobalVariables.getValue(GlobalVariableNames.ZTP_PASSWORD) # Get CVP temp password for ZTP.
        device = Device(device_ip,device_user,device_pass) # Create eAPI session to device via Device library.
        currentVersion = device.runCmds(['enable','show version'])[1]['response']['version'] # Get currently installed version of device
        if currentVersion == image_to_downgrade: # If device version is same as image_to_downgrade var, try to downgrade it.
            if cvp_image == 'undefined':
                EOSImage = get_undefined_image()
            else:
                EOSImage = specific_image
            try:
                print 'Uploading EOS version '+EOSImage+' to device '+device_ip
                device.runCmds(['enable',cvpInstallImage+EOSImage])
                print 'Checking Boot Vars on device '+device_ip
                bootvar = device.runCmds(['enable','show boot'])[1]['response']['softwareImage']
                if bootvar.endswith(EOSImage):
                    print 'Boot Var matches installed image. Rebooting now.'
                    try:
                      device.runCmds(['enable','reload now'])
                    except:
                      pass
            except:
                pass
    else:
        pass
    #end device set-up.

if __name__ == "__main__":
    main()
