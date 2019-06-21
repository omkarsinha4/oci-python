# This script does basic operations on ORACLE instance such as START,STOP,REBOOT,TERMINATE,LAUNCH INSTANCE,GET PUBLIC IP OF INSTANCE,
#RESIZE INSTANCE SIZE BY RESIZING BOOT VOLUME 

import oci
import os.path
import sys
from utilities import utilities
import datetime


class oracle_ops(utilities):

    def __init__(self):
        if os.name == "nt":
            key_file= 'C:\Users\abc\Documents\oci-python\lib\oci_api_key.pem'
        else:
            key_file= '/var/www/oracle/lib/oci_api_key.pem'
        self.configfile = {
            "user": '',             #Enter user OCID here
            "key_file": key_file,   
            "fingerprint": '',      #Enter fingerprint here
            "tenancy": '',          #Enter tenancy OCID here
            "region": 'us-ashburn-1',
            "compartment": '',      #Enter compartment OCID here
            "instance_id": ''       #Enter Instance OCID here. You can also takes instance OCID through command line through sys.argv
         }
        self.instance_metadata = {
        'ssh_authorized_keys': "", #enter ssh key here 
        }
        self.compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        self.virtual_network_client = oci.core.VirtualNetworkClient(self.configfile,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        self.identity_client = oci.identity.IdentityClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)

  # Below function launches a new instance on oracle 
    def launch_oci_instance(self):
            now = datetime.datetime.now()
            string = ('INSTANCE' + format(now))
            self.name= string.replace(" ", "")
            launch_instance_details = oci.core.models.LaunchInstanceDetails(
                display_name=self.name,
                compartment_id=self.configfile['compartment'],
                availability_domain='vNmN:US-ASHBURN-AD-3',
                shape='VM.Standard2.1',
                metadata=self.instance_metadata,
                fault_domain='FAULT-DOMAIN-3',
                source_details=oci.core.models.InstanceSourceViaImageDetails(image_id=''), #Enter a image OCID to be used to launch a new instance on oracle.
                create_vnic_details=oci.core.models.CreateVnicDetails(subnet_id='')) # Enter the subnet OCID 

            
            compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            launch_instance_response = compute_client.launch_instance(launch_instance_details)
            instance_state = oci.wait_until(compute_client,compute_client.get_instance(launch_instance_response.data.id),'lifecycle_state','RUNNING',max_wait_seconds=300,succeed_on_not_found=True).data
            instance = self.compute_client.get_instance(instance_state.id).data
            print instance,'\n\n\n'
            obj1=get_instance_ip()
            self.public_ip = obj1.get_instance_ip_addresses_and_dns_info(instance.id)
            if (instance_state.lifecycle_state == 'RUNNING') :
                return {'status': True,'info':instance,'IP':self.public_ip}
            else:
                return {'status':False,'info':instance}
                
    # Below function terminates an instance on oracle 
    
    def terminate_oci_instance(self):
            compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            instance = self.compute_client.get_instance(self.configfile['instance_id']).data
            compute_client.terminate_instance(instance.id).data
            instance_state=oci.wait_until(compute_client,compute_client.get_instance(instance.id),
                'lifecycle_state',
                'TERMINATED',
                max_wait_seconds=300,
                succeed_on_not_found=True
            ).data

            if (instance_state.lifecycle_state == 'TERMINATED') :
                return {'status': True,'info':instance}
            else:
                return {'status':False,'info':instance}

    # Below function stops an instance on oracle 
    
    def stop_oci_instance(self):
            compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            instance = self.compute_client.get_instance(self.configfile['instance_id']).data
            compute_client.instance_action(instance.id,'STOP')
            instance_state = oci.wait_until(compute_client, compute_client.get_instance(instance.id), 'lifecycle_state','STOPPED',max_wait_seconds=300,succeed_on_not_found=True).data
            if (instance_state.lifecycle_state == 'STOPPED'):
                return {'status': True, 'info': instance}
            else:
                return {'status': False, 'info': instance}

    # Below function starts an instance on oracle
    
    def start_oci_instance(self):
            compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            compute_client.instance_action(self.configfile['instance_id'],'START')
            instance = self.compute_client.get_instance(self.configfile['instance_id']).data
            instance_state = oci.wait_until(compute_client, compute_client.get_instance(instance.id), 'lifecycle_state','RUNNING',max_wait_seconds=300,succeed_on_not_found=True).data
            obj1 = get_instance_ip()
            self.public_ip = obj1.get_instance_ip_addresses_and_dns_info(instance.id)
            if (instance_state.lifecycle_state == 'RUNNING'):
                return {'status': True, 'info': instance, 'IP': self.public_ip}
            else:
                return {'status': False, 'info': instance}

    # Below function reboots an instance on oracle
    
    def reset_oci_instance(self):
        compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        compute_client.instance_action(self.configfile['instance_id'], 'RESET')
        instance = self.compute_client.get_instance(self.configfile['instance_id']).data
        instance_state = oci.wait_until(compute_client, compute_client.get_instance(instance.id), 'lifecycle_state','RUNNING', max_wait_seconds=300, succeed_on_not_found=True).data
        obj1 = get_instance_ip()
        self.public_ip = obj1.get_instance_ip_addresses_and_dns_info(instance.id)
        if (instance_state.lifecycle_state == 'RUNNING'):
                return {'status': True, 'info': instance, 'IP': self.public_ip}
        else:
                return {'status': False, 'info': instance}

    # Below function resizes a boot volume attached to an instance on oracle
    
    def resize_instance(self):

        instance = self.compute_client.get_instance(self.configfile['instance_id']).data
        self.compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        self.volume_attachments = self.compute_client.list_boot_volume_attachments(availability_domain=instance.availability_domain, compartment_id=instance.compartment_id,instance_id=instance.id).data
        self.volume_attachment_id=self.volume_attachments[0].id
        self.volume_id=self.volume_attachments[0].boot_volume_id

        print 'Stopping instance with display name:',instance.display_name,'...........\n'
        obj = oracle_ops()
        instance_info = obj.stop_oci_instance()
        if instance_info['status']:
            print 'STOPPED INSTANCE \n DETACHING VOLUME now..... \n'
            volume_state_detach = obj.detach_volume()
            if volume_state_detach['status']:
                print 'VOLUME DETACHED\n Resizing volume now......\n'
                resize_volume_state= obj.resize_boot_volume()
                if resize_volume_state['status']:
                    print 'Volume resized successfully !!!'
                    print '\nNew size of the instance is now:',resize_volume_state['info']
                    print '\nattaching volume back to instance....\n'
                    volume_state_attach = obj.attach_volume()
                    if volume_state_attach['status']:
                        print 'Volume attached successfully\n STARTING instance now....\n'
                        start_instance= obj.start_oci_instance()
                        if start_instance['status']:
                            print 'Instance started successfully !!!'
                            print 'Instance Public IP:',start_instance['IP']
                            return {'status' : True}
                        else:
                            print 'There was a problem starting instance'
                            return {'status': True}
                    else:
                        print 'volume attachment failed'
                        return {'status': True}
                else:
                    print 'resize volume failed'
                    return {'status': True}
            else:
                print 'detach volume failed'
                return {'status': True}
        else:
            print 'Stopping instance failed'
            return {'status': True}

    # Below function detaches a boot volume from an instance on oracle
    
    def detach_volume(self):
        self.compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        instance = self.compute_client.get_instance(self.configfile['instance_id']).data
        self.volume_attachments = self.compute_client.list_boot_volume_attachments(availability_domain=instance.availability_domain, compartment_id=instance.compartment_id,instance_id=instance.id).data
        self.volume_attachment_id = self.volume_attachments[0].id
        self.volume_id = self.volume_attachments[0].boot_volume_id

        #detach_instance_boot_volume_details = {'bootVolumeId': self.volume_id, 'instanceId': instance.id}
        self.detach_volume_state = self.compute_client.detach_boot_volume(self.volume_attachment_id)
        update_volume_state = oci.wait_until(self.compute_client,self.compute_client.get_boot_volume_attachment(self.volume_attachment_id),'lifecycle_state', 'DETACHED', max_wait_seconds=300).data

        if (update_volume_state.lifecycle_state == 'DETACHED'):
            return {'status': True}
        else:
            return {'status': False}
    
    # Below function updates the size of a boot volume of an instance on oracle
    
    def resize_boot_volume(self):
        instance = self.compute_client.get_instance(self.configfile['instance_id']).data
        self.volume_attachments = self.compute_client.list_boot_volume_attachments(availability_domain=instance.availability_domain, compartment_id=instance.compartment_id,instance_id=instance.id).data
        self.volume_attachment_id = self.volume_attachments[0].id
        self.volume_id = self.volume_attachments[0].boot_volume_id

        self.blockstorageclient = oci.core.BlockstorageClient(self.configfile,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        a=self.blockstorageclient.get_boot_volume(self.volume_id).data
        update_instance_boot_volume_details={'sizeInGBs':a.size_in_gbs+10,'displayName':a.display_name}
        self.blockstorageclient.update_boot_volume(self.volume_id,update_instance_boot_volume_details)
        update_volume_state=oci.wait_until(self.blockstorageclient,self.blockstorageclient.get_boot_volume(self.volume_id),'lifecycle_state','AVAILABLE',max_wait_seconds=300).data
        
        if (update_volume_state.lifecycle_state == 'AVAILABLE'):
            return {'status' : True,'info' : update_volume_state.size_in_gbs}
        else:
            return {'status' : False}
    
    # Below function attaches a boot volume from an instance on oracle
    
    def attach_volume(self):
        self.compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        instance = self.compute_client.get_instance(self.configfile['instance_id']).data
        self.volume_attachments = self.compute_client.list_boot_volume_attachments(availability_domain=instance.availability_domain, compartment_id=instance.compartment_id,instance_id=instance.id).data
        self.volume_attachment_id = self.volume_attachments[0].id
        self.volume_id = self.volume_attachments[0].boot_volume_id


        attach_instance_boot_volume_details={'bootVolumeId':self.volume_id ,'instanceId':instance.id}
        self.attach_volume_state=self.compute_client.attach_boot_volume(attach_instance_boot_volume_details)
        update_volume_state =oci.wait_until(self.compute_client,self.compute_client.get_boot_volume_attachment(self.volume_attachment_id),'lifecycle_state','ATTACHED', max_wait_seconds=300).data
        if (update_volume_state.lifecycle_state == 'ATTACHED'):
            return {'status' : True}
        else:
            return {'status' : False}

    # Below function list instances on oracle
    
    def list_instances(self):
        instance = self.compute_client.get_instance(self.configfile['instance_id']).data
        compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        self.instances=compute_client.list_instances(compartment_id=instance.compartment_id).data
        return self.instances

#Below class gets the information on IP's of an instance

class get_instance_ip(oracle_ops):

    def __init__(self):
        self.subnet_info = {}
        self.vcn_info = {}

        self.private_ip_to_public_ip = {}
        if os.name == "nt":
            key_file= 'C:\Users\abc\Documents\oci-python\lib\oci_api_key.pem'
        else:
            key_file= '/var/www/oracle/lib/oci_api_key.pem'
        self.configfile = {
            "user": '',
            "key_file": key_file,
            "fingerprint": '',
            "tenancy": '',
            "region": 'us-ashburn-1',
            "compartment": '',
            "instance_id": ''
         }
        self.compute_client = oci.core.ComputeClient(self.configfile, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        self.virtual_network_client = oci.core.VirtualNetworkClient(self.configfile,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        self.identity_client = oci.identity.IdentityClient(self.configfile,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)

    def get_reserved_public_ips_for_compartment(self,compartment_id):

        return oci.pagination.list_call_get_all_results(self.virtual_network_client.list_public_ips,'REGION',compartment_id).data

    def load_reserved_public_ips_for_all_compartments(self):

        compartments = oci.pagination.list_call_get_all_results(
            self.identity_client.list_compartments,
            self.configfile['compartment']
        ).data
        compartment_ids = [c.id for c in compartments]
        if self.configfile['compartment'] not in compartment_ids:
            compartment_ids.append(self.configfile['compartment'])

        for compartment_id in compartment_ids:
            public_ips = self.get_reserved_public_ips_for_compartment(compartment_id)
            private_ip_to_public_ip_for_compartment = {p.private_ip_id: p for p in public_ips}
            self.private_ip_to_public_ip.update(private_ip_to_public_ip_for_compartment)

    def get_subnet_info(self, subnet_id):
        subnet = self.virtual_network_client.get_subnet(subnet_id).data

        if subnet.vcn_id not in self.vcn_info:
            self.vcn_info[subnet.vcn_id] = self.virtual_network_client.get_vcn(subnet.vcn_id).data

        return subnet

    def get_instance_ip_addresses_and_dns_info(self,instance_id):
        instance_info = {
            'private_ips': [],
            'dns_info': [],
            'public_ips': []
        }

        instance = self.compute_client.get_instance(instance_id).data

        vnic_attachments = oci.pagination.list_call_get_all_results(self.compute_client.list_vnic_attachments,compartment_id=instance.compartment_id,instance_id=instance.id).data

        vnics = [self.virtual_network_client.get_vnic(va.vnic_id).data for va in vnic_attachments]
        for vnic in vnics:
            if vnic.public_ip:
                instance_info['public_ips'].append(vnic.public_ip)

            if vnic.subnet_id not in self.subnet_info:
                self.subnet_info[vnic.subnet_id] = self.get_subnet_info(vnic.subnet_id)
            private_ips_for_vnic = oci.pagination.list_call_get_all_results(self.virtual_network_client.list_private_ips,vnic_id=vnic.id).data

            for private_ip in private_ips_for_vnic:
                instance_info['private_ips'].append(private_ip.ip_address)

                subnet = self.subnet_info[
                    private_ip.subnet_id]  # Could also use vnic_id rather than private_ip.subnet_id

                vcn = self.vcn_info[subnet.vcn_id]
                if subnet.dns_label and vcn.dns_label and private_ip.hostname_label:
                    instance_info['dns_info'].append(
                        '{}.{}.{}.oraclevcn.com'.format(private_ip.hostname_label, subnet.dns_label, vcn.dns_label)
                    )
                if not self.private_ip_to_public_ip:
                    self.load_reserved_public_ips_for_all_compartments()

                if private_ip.id in self.private_ip_to_public_ip:  # This is (F1)
                    print('Found public IP mapping for private IP in list. Public IP details: {}'.format(
                        self.private_ip_to_public_ip[private_ip.id]))

                try:
                    public_ip = self.virtual_network_client.get_public_ip_by_private_ip_id(
                        oci.core.models.GetPublicIpByPrivateIpIdDetails(
                            private_ip_id=private_ip.id
                        )
                    ).data

                    if public_ip.ip_address not in instance_info['public_ips']:
                        instance_info['public_ips'].append(public_ip.ip_address)
                except oci.exceptions.ServiceError as e:
                    if e.status == 404:
                        print('No public IP mapping found for private IP: {} ({})'.format(private_ip.id,private_ip.ip_address))
                    else:
                        print('Unexpected error when retrieving public IPs: {}'.format(str(e)))

        return instance_info['public_ips']

# Below is the calls to different functions of oracle_ops and get_instance_ip classes.

if __name__ == "__main__":

    obj=oracle_ops()
    #obj1=get_instance_ip()
    ######################## LAUNCH INSTANCE ############################
    '''Launch instance function'''
    '''instance_info = obj.launch_oci_instance()
    id = instance_info['info']
    display_name = instance_info['info'].display_name
    if instance_info['status']:
        print('\nLaunched instance')
        print('===========================')
        print('\nRunning instance')
        print('===========================')
        print "Instance details:\nInstance_name:",display_name,'\ninstance OCID:',id,'\ninstance info:',instance_info['info']
        print "Public IP for instance created :\n", instance_info['IP']
    else:
         print ("Failed to launch instance") 
    '''
    ########################## STOP INSTANCE ############################
    ''' Stop Instance Function'''
    '''instance_info = obj.stop_oci_instance()
    id = instance_info['info'].id
    display_name = instance_info['info'].display_name
    if instance_info['status']:
        print '\nStopped instance'
        print '==========================='
        print 'Stopped instance with name:',display_name,'\n and with OCID:\t', id,'successfully'
    else:
        print "Failed to stop instance as instance is already in stopped state or no such instance exist !"
    '''
    ########################### START INSTANCE ##########################
    ''' Start Instance Function '''
    '''instance_info = obj.start_oci_instance()
    id = instance_info['info'].id
    display_name = instance_info['info'].display_name
    if instance_info['status']:
        print '\nStarted instance'
        print '==========================='
        print 'Started instance with name:',display_name,'\n and with OCID:\t', id, 'successfully\n\n'
        #print 'Instance details:',instance_info['info'],'\n\n'
        print 'Public IP of instance:\t\t\t',instance_info['IP']
    else:
        print "Failed to start instance as instance is already in running state or no such instance exist !"
    '''
    ########################## REBOOT INSTANCE ##########################
    ''' Reset Instance Function '''
    '''instance_info = obj.reset_oci_instance()
    id = instance_info['info'].id
    display_name = instance_info['info'].display_name
    if instance_info['status']:
        print '\nRebooted instance'
        print '==========================='
        print 'Rebooted instance with name:',display_name,'\n and with OCID:\t', id, 'successfully\n\n'
       #print 'Instance details:',instance_info['info'],'\n\n'
        print 'Public IP of instance:\t\t\t', instance_info['IP']
    else:
        print "Failed to start instance as instance is already in running state or no such instance exist !"
    '''
    ############################ TERMINATE INSTANCE ##########################
    '''Terminate instance function '''
    '''instance_info = obj.terminate_oci_instance()
    id= instance_info['info'].id
    display_name = instance_info['info'].display_name
    if instance_info['status']:
        print 'Instance with name:',display_name,'\n and with OCID:\t', id, 'terminated successfully'
    else:
        print "Failed to terminate instance with instance id:",id,"as the instance is already terminated or no such instance exist"
    '''
    ######################### LIST INSTANCES #############################
    '''List of Instances'''
    '''instances_list = obj.list_instances()
    if instances_list:
        print 'Below is the list of instance:\n\n',instances_list
    else:
        print 'No instances found ,please check compartment id given is correct !!'
    '''
    ######################## RESIZE INSTANCE ############################
    '''Resize instance function
    instance_info=obj.resize_instance()
    if (instance_info['status']):
        print '********************** INSTANCE RESIZE OPERATION COMPLETED SUCCESSFULLY *********************** !!!!'
        #print 'New size of the instance is now:',instance_info['info']
    else:
        print 'Instance resize failed !!!'
    '''
    
    
