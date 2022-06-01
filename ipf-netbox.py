#!/usr/bin/python3
# Python3 sample code to read inventory data from IP Fabric and to modify NetBox inventory.

from ipfabric import IPFClient
from modules.netbox import *
import pynetbox

IPF_SERVER = "https://ipf_server"  # demo4
IPF_TOKEN = ""  # api_token
IPF_SNAPSHOT = '$last' # or uuid
IPF_CERT_VERIFY = True
NB_SERVER = "http://netbox_server:8000/"
NB_TOKEN = "" # api_token
NB_CERT_VERIFY = False


if __name__ == "__main__":
    '''
    Available dcim methods to put data in Netbox (and their couterparts in IP Fabric):
        - sites (needs name & slug) = sites
        - manufacturers (needs name & slug) = vendors
        - platforms (needs name & slug) = platforms
        - device-roles (needs name & slug) = devType
        - device-types (needs model & slug & manufacturerID) = vendor, model
        - devices (needs name & slug & siteID & device-roleID & device-typeID & platformID)
    '''
    # IP Fabric - Initiate IPFClient
    ipf_api = IPFClient(
        base_url=IPF_SERVER,
        token=IPF_TOKEN,
        snapshot_id=IPF_SNAPSHOT,
        verify=IPF_CERT_VERIFY,
    )
    # NetBox - Initiate pynetbox.api
    netbox_api = pynetbox.api(NB_SERVER, token=NB_TOKEN)
    # netbox_api.http_session.verify = NB_CERT_VERIFY

    # IP Fabric - Collecting parameters
    # ipf_devices = ipf_api.inventory.devices.all(filters={})
    # ipf_interfaces = ipf_api.inventory.interfaces.all()
    # test_hostname = [h for h in ipf_devices if h['hostname'] == 'Hostname1']
    # ipf_vendors = list(set([v['vendor'] for v in ipf_api.inventory.devices.all(filters={})]))
    # ipf_platforms = list(set([p['platform'] for p in ipf_api.inventory.devices.all(filters={})]))
    # ipf_devtype = list(set([d['devType'] for d in ipf_api.inventory.devices.all(filters={})]))

    # # Example 01 - Adding devices to NetBox (JSON to NetBox)
    # addNetboxDevices(ipf_devices, netbox_api)

    # # Example 02 - Adding sites
    # addNetboxData(['L890'], 'sites', netbox_api)
    # print(getNetboxData(netbox_api, 'sites'))

    # # Example 03 - Adding manufacturers
    # addNetboxData(['juniper'], 'manufacturers', netbox_api)
    # print(getNetboxData(netbox_api, 'manufacturers'))

    # # Example 04 - Adding device roles
    # addNetboxData(['firewall'], 'device-roles', netbox_api)
    # print(getNetboxData(netbox_api, 'device-roles'))

    # # Example 05 - Adding platforms
    # addNetboxData(['ios-xe'], 'platforms', netbox_api)
    # print(getNetboxData(netbox_api, 'platforms'))
    
    # # Example 06 - Delete NetBox element (site, device, manufacturer, ...)
    # deleteNetboxData(['ios-xe'], 'platforms', netbox_api)
    # print(getNetboxData(netbox_api, 'platforms'))

    # # Example 7 - Adding device types
    # dev_types = [{'vendor': 'cisco', 'model': 'WS-C3750E-24TD'} ] 
    # addNetboxDevTypes(dev_types, netbox_api)
    # print(getNetboxData(netbox_api, 'device-types'))

