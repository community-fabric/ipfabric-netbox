import re
import sys
from rich import print

def getNetboxData(netbox_api, dcim_method):
    """Loading netbox_api returns list of items in Netbox
        input: netbox_api <class>, dcim_method (string)
        return: netbox_data (list)
    """
    netbox_data = getattr(netbox_api.dcim, dcim_method).all()
    return [s for s in netbox_data]

def deleteNetboxData(input_list, dcim_method, netbox_api):
    """Adds any data to Netbox if only name and slug are required
        input: input_list (list), dcim_method 'string', netbox_api <class>
        return: netbox_elements (RecordSet)
    """
    for data in input_list:
        data_check = getattr(netbox_api.dcim, dcim_method).get(name=data)
        if not data_check:
            print("[yellow]  The {}: {} is not in Netbox, nothing to delete.[/yellow]"
            .format(dcim_method, data))
        else:
            data_check.delete()
            print("[green]  Deleting site {} from Netbox[/green]".format(data))
        return getattr(netbox_api.dcim, dcim_method).all()

def addNetboxData(input_list, dcim_method, netbox_api):
    """Adds any data to Netbox if only name and slug are required
        input: input_list (list), dcim_method 'string', netbox_api <class>
        return: netbox_elements (RecordSet)
    """
    return_ids = list()
    for data in input_list:
        data_check = getattr(netbox_api.dcim, dcim_method).get(name = data)
        if not data_check:
            data_attributes = {
                "name": data,
                "slug": data,
            }
            create_entry = dict(getattr(netbox_api.dcim, dcim_method).create(data_attributes))
            print("[green]  New {} added into Netbox: {} and ID: {}[/green]"
            .format(dcim_method, create_entry['name'], create_entry['id']))
            return_ids.append(create_entry['id'])
        else:
            print("[yellow]  The {}' item is already in Netbox: {} [/yellow]".format(dcim_method, data))
            return_ids.append(data_check.id)
    return return_ids

def addNetboxDevTypes(devtypes_input, netbox_api):
    """Deletes sites in Netbox if they exist
        input: detypes_input (list), netbox_api <class>
        return: netbox_device_types (RecordSet)
    """
    return_ids = list()
    for devtype in devtypes_input:
        manufacturer = devtype['vendor']
        model = devtype['model'] if (devtype['model'] != '') else 'unspecified'

        # Checking if manufacturer exists in Netbox 
        if not netbox_api.dcim.manufacturers.get(name=manufacturer):
            addNetboxData([manufacturer], 'manufacturers', netbox_api)

        # First we need to get proper manufacturer's ID
        manu_id = netbox_api.dcim.manufacturers.get(name=manufacturer).id

        if not (netbox_api.dcim.device_types.get(model=model, manufacturer=manufacturer)):
            devtype_vals = {
                "model": model,
                "slug": model,
                "manufacturer": manu_id,
            }
            added_devtype = dict(netbox_api.dcim.device_types.create(devtype_vals))
            print("[green]  Added new devtype: {}, under manufacturer: {} with ID: {} [/green]"
            .format(added_devtype['model'], added_devtype['manufacturer']['display'], added_devtype['id']))
            return_ids.append(added_devtype['id'])
        else:
            print("[yellow]  The devtype: {} is already in Netbox [/yellow]"
            .format(model))
            return_ids.append(netbox_api.dcim.device_types.get(model=model, manufacturer=manufacturer).id)
    return return_ids

def checkNetboxData(nb_data, dcim_method, param, nb_api):
    if type(param) == str:
        if param not in nb_data:
            param_ids = addNetboxData([param], dcim_method, nb_api)
            return param_ids[0]
        else:
            return getattr(nb_api.dcim, dcim_method).get(name=param).id
    else:
        if param['model'] not in nb_data:
            param_ids = addNetboxDevTypes([param], nb_api)
            return param_ids[0]
        else:
            return getattr(nb_api.dcim, dcim_method).get(model=param['model'], manufacturer=param['vendor']).id

def cleanString(input_string, clue='X'):
    """Cleaning strings before importing to NetBox is needed due to NB rules. Need to be considered when comparing inventories.
        input: input_string 'string', clue 'string' options are [X, L, U]
        return: return_string 'string'
    """
    if not input_string: return 'unspecified'
    return_string = re.sub('[^A-Za-z0-9-_]+', '', input_string)
    if clue == 'L': return return_string.lower()
    elif clue == 'U': return return_string if (return_string != '') else 'unspecified'
    else: return return_string

def addNetboxInterfaces(ipf_interfaces, netbox_api):
    """Loads list of dictionaries (ipf_interfaces) and adds them one by one to Netbox.
        input: ipf_interfaces (list), netbox_api <class>
    """
    # Fetch existing Netbox devices into a dict {'hostname': 'id'}
    nb_devices_dict = {}
    for nb_device in getNetboxData(netbox_api, 'devices'):
        device_dict = dict(nb_device)
        nb_devices_dict.update([(device_dict["name"], device_dict["id"])])
    # Fetch existing Netbox interfaces into a dict {'hostname::intf': 'intfId'}
    nb_interfaces_dict = {}
    for nb_intf in getNetboxData(netbox_api, 'interfaces'):
        intf_dict = dict(nb_intf)
        nb_interfaces_dict.update(
            [(intf_dict["device"]["name"] + "::" + intf_dict["name"], intf_dict["id"])]
        )

    # Iterate interfaces from IP Fabric and add them to NetBox
    print("[green] Adding Interfaces:[/green]")
    for ipf_intf in ipf_interfaces:
        # Set interface parameters
        int_name = ipf_intf["nameOriginal"] if ipf_intf["nameOriginal"] is not None else ipf_intf['intName']
        int_desc = ipf_intf["dscr"] if ipf_intf["dscr"] is not None else "<empty>"
        int_type = "1000base-t" # There's not alternative parameter to reflect NetBox's types
        int_hostname = cleanString(ipf_intf["hostname"])

        if int_hostname + "::" + int_name not in nb_interfaces_dict.keys():
            # Test if the interface is enabled
            if (
                ipf_intf["l1"] == "down"
                and ipf_intf["l2"] == "down"
                and ipf_intf["reason"] == "admin"
            ):
                int_enabled = False
            else:
                int_enabled = True
            try:
                intf_attributes = {
                    "device": nb_devices_dict[int_hostname], # Device ID from NetBox
                    "name": int_name,
                    "label": int_desc,
                    "enabled": int_enabled,
                    "type": int_type,
                    "description": int_desc,
                }
                added_intf = dict(netbox_api.dcim.interfaces.create(intf_attributes))
                print("  [green]Adding interface {} for hostname {}[/green]"
                .format(int_name, int_hostname))

                # Check if this interface has a Primary IP Address and is the loginIP of the device
                if ipf_intf["primaryIp"] is not None and ipf_intf["primaryIp"] == ipf_intf["loginIp"]:
                    intf_id = added_intf["id"]
                    ip_add = ipf_intf["loginIp"]
                    #search all IPs in Netbox matching this IP address
                    nb_ip = netbox_api.ipam.ip_addresses.filter(address=ip_add)
                    # we will assign the 1st non-assigned one
                    update_nb_login_ip = False
                    if len(nb_ip) >= 1:
                        for ip in nb_ip:
                            if ip.assigned_object is None:
                                #print(f"Found at least one available entry: {ip}")
                                nb_ip = ip
                                update_nb_login_ip = True
                                break
                            else:
                                print("  IP is already assigned: {}".format(ip))
                    else:
                        print("  No match for IP address {} in Netbox:".format(ip_add))
                    
                    if update_nb_login_ip:
                        nb_ip.assigned_object_id = intf_id
                        nb_ip.assigned_object_type = "dcim.interface"
                        nb_ip.save()
                        # make it primary for the device
                        devId = nb_devices_dict[int_hostname]
                        nb_device = netbox_api.dcim.devices.get(devId)
                        nb_device.primary_ip4 = nb_ip
                        nb_device.primary_ip = nb_ip
                        nb_device.save()
                        print("  [blue]IP: {} assigned to {}[/blue]"
                        .format(nb_ip, int_hostname))
            except KeyError as exc:
                print("KeyError: Device {} not found in Netbox, err: {}".format(int_hostname, exc))
        else:
            print("  [yellow]Device {} with interface {} is already in NetBox[/yellow]"
            .format(int_hostname, int_name))

def addNetboxDevices(ipf_devices, netbox_api):
    """Loads list of dictionaries (ipf_devices) and adds them one by one to Netbox. If vendor, platform or devtype doesn't exist, it will be created.
        input: ipf_devices (list), netbox_api <class>
        return: netbox_devices (RecordSet)
    """
    def iterateDcim(dcim_method, nb_api):
        return [str(d) for d in getattr(nb_api.dcim, dcim_method).all()]

    print(' Reading parameters from NetBox..')
    nb_devices = iterateDcim('devices', netbox_api)
    nb_sites = iterateDcim('sites', netbox_api)
    nb_platforms = iterateDcim('platforms', netbox_api)
    nb_types = iterateDcim('device_types', netbox_api) 
    nb_roles = iterateDcim('device_roles', netbox_api)
    
    for ipfdev in ipf_devices:
        hostname = cleanString(ipfdev['hostname']) # Will include only allowed chars
        site = cleanString(ipfdev['siteName'], 'L') # Will be lowercase
        vendor = cleanString(ipfdev['vendor'], 'L') # Will be lowercase
        platform = cleanString(ipfdev['platform'], 'L') # Will be lowercase
        model = cleanString(ipfdev['model'], 'U') # Will be undefined if none
        devtype = cleanString(ipfdev['devType'])

        if hostname not in nb_devices:
            try:
                # Generating device values
                dev_vals = {
                    "name": hostname,
                    'site': checkNetboxData(nb_sites, 'sites', site, netbox_api),
                    'platform': checkNetboxData(nb_platforms, 'platforms', platform, netbox_api),
                    "primary_ip": ipfdev["loginIp"] if ipfdev["loginIp"] is not None else '',
                    "serial": ipfdev["snHw"] if len(ipfdev["snHw"])<50 else ipfdev["snHw"][-50:],
                    'device_type': checkNetboxData(nb_types, 'device_types', {'vendor': vendor, 'model': model}, netbox_api),
                    'device_role': checkNetboxData(nb_roles, 'device_roles', devtype, netbox_api)
                }
                # Adding device to Netbox           
                added_dev = dict(netbox_api.dcim.devices.create(dev_vals))

                print("[green] Device: {} was added to Netbox with ID: {} [/green]"
                .format(added_dev['name'], added_dev['id']))
            except:
                print('[red] Unable do add hostname: {} [/red]'.format(hostname))
                print('Unexpected error:', sys.exc_info())
        else:
            print("[yellow] Device: {} is already in Netbox.[/yellow]".format(hostname))
    return getNetboxData(netbox_api, 'devices')