import sys
import redfish
import subprocess
import time
import json
import numpy

class ilohelper:
    def __init__(self, iLO, login_account, login_password, targetip):
        self.target_ip = targetip
        self.iLO_host = f"https://{iLO}"
        self.login_account = login_account
        self.login_password = login_password
        self.mintemp = 0
        self.maxtemp = 0
        print("Initialized")
        self.client = redfish.redfish_client(
            base_url=self.iLO_host,
            username=self.login_account,
            password=self.login_password,
            default_prefix='/redfish/v1'
        )
        try:
            self.client.login(auth="basic")
            print("Login successful.")
        except Exception as e:
            print(f"Error during login: {str(e)}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Destroying object")
        if self.client:
            self.client.logout()
            print("Logout successful.")

    def get_temperatures(self):
        if self.client:
            try:
                print("------> Getting Temperatures <-------")
                response = self.client.get("/redfish/v1/Chassis/1/Thermal/")
                sensors_data = response.dict["Temperatures"]
                temperatures = []
                for sensor in sensors_data:
                    sensor_value = sensor["ReadingCelsius"]
                    print(f"Sensor {sensor['Name']} has {sensor_value} degrees")
                    temperatures.append(sensor_value)
                    self.mintemp = min(sensor_value, self.mintemp) if sensor_value < self.mintemp else self.mintemp
                    self.maxtemp = max(sensor_value, self.maxtemp) if sensor_value > self.maxtemp else self.maxtemp
                self.avgtemp = numpy.mean(temperatures)
                print(f"Mintemp: {self.mintemp}")
                print(f"Maxtemp: {self.maxtemp}")
                print(f"Avgtemp: {self.avgtemp}")
                print("will return: ")
                print(temperatures)
                return temperatures
            except Exception as e:
                print(f"Error retrieving temperature data: {str(e)}")
                return {}
        else:
            return {}

    def get_server_status(self):
        if self.client:
            try:
                self.get_temperatures()
                print("------> Getting ServerStatus <-------")
                response = self.client.get("/redfish/v1/Systems/1")
                status = response.dict
                power_state = status["PowerState"]
                self.power_state = False if power_state == "Off" else True
                self.memory = status["MemorySummary"]["TotalSystemMemoryGiB"]
                self.cpu = status["ProcessorSummary"]
                print(f"Power state: {power_state}")
                print(f"Memory: {self.memory}")
                print(f"CPU: {self.cpu}")
                return status
            except Exception as e:
                print(f"Error retrieving status: {str(e)}")
                return None
        else:
            return None

    def start_server(self):
        if self.client:
            try:
                print("------> Starting Server <-------")
                response = self.client.post('/redfish/v1/Systems/1/Actions/ComputerSystem.Reset/', body={'ResetType': 'PushPowerButton'})
                print(response)
            except Exception as e:
                print(f"Error starting server: {str(e)}")

    def stop_server(self):
        if self.client:
            try:
                print("------> Stopping Server <-------")
                response = self.client.post('/redfish/v1/Systems/1/Actions/ComputerSystem.Reset/', body={'ResetType': 'ForceOff'})
                print(response)
            except Exception as e:
                print(f"Error starting server: {str(e)}")

    def waitForBoot(self):
        print("------> Waiting until OS booted <-------")
        ttl_found = False
        max_attempts = 100  # Maximum number of ping attempts
        attempt_count = 0
        self.get_server_status()
        print(self.power_state)
        if self.power_state is not True:
            self.start_server()
            print("Waiting until turned on")
            print("....waiting 5 seconds")
            time.sleep(5)
            
            while not ttl_found and attempt_count < max_attempts:
                try:
                    # Executes the ping command and reads the output
                    result = subprocess.run(['ping', '-c', '1', self.target_ip], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                    print(result)
                    # Looks for "time=" in the output, indicating a TTL value
                    if "0% packet loss" in result.stdout:
                        print("Server has booted")
                        ttl_found = True
                    else:
                        print("Not yet ready...no IP...waiting for DHCP ACK...")
                except Exception as e:
                    print(f"Error pinging: {str(e)}")
                    break
                
                attempt_count += 1
                time.sleep(1)  # Delay between attempts
            if not ttl_found:
                print("Too many retries. Stopping script and logging out")
            else:
                print(f"Finished after {attempt_count} seconds")
        else:
            print("Server is already turned on")

# Example usage of the class
def execute_command(command, client):
    if command == "temperatures":
        client.get_temperatures()
    elif command == "serverStatus":
        client.get_server_status()
    elif command == "startServer":
        client.start_server()
    elif command == "stopServer":
        client.stop_server()
    elif command == "waitForBoot":
        client.waitForBoot()
    else:
        print("Invalid command specified.")

if __name__ == "__main__":
    import sys

    command = sys.argv[1]
    iLO = sys.argv[2]  # "ILO_Hostname_Or_IP"
    login_account = sys.argv[3]  # "admin"
    login_password = sys.argv[4]  # "Password"
    targetIp = sys.argv[5] if isinstance(sys.argv[5], str) else 0  # server IP
    client = ilohelper(iLO, login_account, login_password, targetIp)

    # Check if the command is valid and execute it
    if command in ["temperatures", "serverStatus", "startServer", "stopServer", "waitForBoot"]:
        execute_command(command, client)
    else:
        print("Invalid command. Please choose from the following options: get_temperatures, get_server_status, start_server, stop_server, ping_until_boot.")


iloExample={
    "@odata.context": "/redfish/v1/$metadata#Systems/Members/$entity",
    "@odata.id": "/redfish/v1/Systems/1/",
    "@odata.type": "#ComputerSystem.1.0.1.ComputerSystem",
    "Actions": {
        "#ComputerSystem.Reset": {
            "ResetType@Redfish.AllowableValues": [
                "On",
                "ForceOff",
                "ForceRestart",
                "Nmi",
                "PushPowerButton"
            ],
            "target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset/"
        }
    },
    "AssetTag": "                                ",
    "BiosVersion": "P72 02/10/2014",
    "Boot": {
        "BootSourceOverrideEnabled": "Disabled",
        "BootSourceOverrideSupported": [
            "None",
            "Floppy",
            "Cd",
            "Hdd",
            "Usb",
            "Utilities",
            "BiosSetup",
            "Pxe"
        ],
        "BootSourceOverrideTarget": "None"
    },
    "Description": "Computer System View",
    "EthernetInterfaces": {
        "@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/"
    },
    "HostName": "Big",
    "Id": "1",
    "IndicatorLED": "Off",
    "Links": {
        "Chassis": [
            {
                "@odata.id": "/redfish/v1/Chassis/1/"
            }
        ],
        "ManagedBy": [
            {
                "@odata.id": "/redfish/v1/Managers/1/"
            }
        ]
    },
    "LogServices": {
        "@odata.id": "/redfish/v1/Systems/1/LogServices/"
    },
    "Manufacturer": "HPE",
    "MemorySummary": {
        "Status": {
            "HealthRollup": "OK"
        },
        "TotalSystemMemoryGiB": 96
    },
    "Model": "ProLiant ML350p Gen8",
    "Name": "Computer System",
    "Oem": {
        "Hp": {
            "@odata.type": "#HpComputerSystemExt.1.2.2.HpComputerSystemExt",
            "Actions": {
                "#HpComputerSystemExt.PowerButton": {
                    "PushType@Redfish.AllowableValues": [
                        "Press",
                        "PressAndHold"
                    ],
                    "target": "/redfish/v1/Systems/1/Actions/Oem/Hp/ComputerSystemExt.PowerButton/"
                },
                "#HpComputerSystemExt.SystemReset": {
                    "ResetType@Redfish.AllowableValues": [
                        "ColdBoot",
                        "AuxCycle"
                    ],
                    "target": "/redfish/v1/Systems/1/Actions/Oem/Hp/ComputerSystemExt.SystemReset/"
                }
            },
            "Bios": {
                "Backup": {
                    "Date": "02/10/2014",
                    "Family": "P72",
                    "VersionString": "P72 02/10/2014"
                },
                "Bootblock": {
                    "Date": "03/05/2013",
                    "Family": "P72",
                    "VersionString": "P72 03/05/2013"
                },
                "Current": {
                    "Date": "02/10/2014",
                    "Family": "P72",
                    "VersionString": "P72 02/10/2014"
                },
                "UefiClass": 0
            },
            "DeviceDiscoveryComplete": {
                "AMSDeviceDiscovery": "NoAMS",
                "DeviceDiscovery": "vAuxDeviceDiscoveryComplete",
                "SmartArrayDiscovery": "Complete"
            },
            "IntelligentProvisioningIndex": 3,
            "IntelligentProvisioningLocation": "System Board",
            "IntelligentProvisioningVersion": "N/A",
            "Links": {
                "BIOS": {
                    "@odata.id": "/redfish/v1/Systems/1/Bios/"
                },
                "EthernetInterfaces": {
                    "@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/"
                },
                "FirmwareInventory": {
                    "@odata.id": "/redfish/v1/Systems/1/FirmwareInventory/"
                },
                "Memory": {
                    "@odata.id": "/redfish/v1/Systems/1/Memory/"
                },
                "NetworkAdapters": {
                    "@odata.id": "/redfish/v1/Systems/1/NetworkAdapters/"
                },
                "PCIDevices": {
                    "@odata.id": "/redfish/v1/Systems/1/PCIDevices/"
                },
                "PCISlots": {
                    "@odata.id": "/redfish/v1/Systems/1/PCISlots/"
                },
                "SmartStorage": {
                    "@odata.id": "/redfish/v1/Systems/1/SmartStorage/"
                },
                "SoftwareInventory": {
                    "@odata.id": "/redfish/v1/Systems/1/SoftwareInventory/"
                }
            },
            "PostState": "PowerOff",
            "PowerAllocationLimit": 460,
            "PowerAutoOn": "Restore",
            "PowerOnDelay": "Minimum",
            "PowerRegulatorMode": "Dynamic",
            "PowerRegulatorModesSupported": [
                "OSControl",
                "Dynamic",
                "Max",
                "Min"
            ],
            "TrustedModules": [
                {
                    "Status": "NotPresent"
                }
            ],
            "VirtualProfile": "Inactive"
        }
    },
    "PowerState": "Off",
    "ProcessorSummary": {
        "Count": 2,
        "Model": " Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz      ",
        "Status": {
            "HealthRollup": "OK"
        }
    },
    "Processors": {
        "@odata.id": "/redfish/v1/Systems/1/Processors/"
    },
    "SKU": "xxxxx    ",
    "SerialNumber": "xxxxx      ",
    "Status": {
        "Health": "Warning",
        "State": "Disabled"
    },
    "SystemType": "Physical",
    "UUID": "xxxx"
}

thermalobject={
    "@odata.context": "/redfish/v1/$metadata#Chassis/Members/1/Thermal$entity",
    "@odata.id": "/redfish/v1/Chassis/1/Thermal/",
    "@odata.type": "#Thermal.1.1.0.Thermal",
    "Fans": [
        {
            "FanName": "Fan 1",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpServerFan.1.0.0.HpServerFan",
                    "Location": "System"
                }
            },
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            }
        },
        {
            "FanName": "Fan 2",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpServerFan.1.0.0.HpServerFan",
                    "Location": "System"
                }
            },
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            }
        },
        {
            "FanName": "Fan 3",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpServerFan.1.0.0.HpServerFan",
                    "Location": "System"
                }
            },
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            }
        },
        {
            "FanName": "Fan 4",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpServerFan.1.0.0.HpServerFan",
                    "Location": "System"
                }
            },
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            }
        }
    ],
    "Id": "Thermal",
    "Name": "Thermal",
    "Temperatures": [
        {
            "Name": "01-Inlet Ambient",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 1,
                    "LocationYmm": 0
                }
            },
            "PhysicalContext": "Intake",
            "ReadingCelsius": 21,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 42,
            "UpperThresholdFatal": 46
        },
        {
            "Name": "02-CPU 1",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 4,
                    "LocationYmm": 8
                }
            },
            "PhysicalContext": "CPU",
            "ReadingCelsius": 40,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "03-CPU 2",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 10,
                    "LocationYmm": 7
                }
            },
            "PhysicalContext": "CPU",
            "ReadingCelsius": 40,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "04-P1 DIMM 1-6",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 11,
                    "LocationYmm": 10
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 28,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 87,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "05-P1 DIMM 7-12",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 11,
                    "LocationYmm": 4
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 30,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 87,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "06-P2 DIMM 1-6",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 4,
                    "LocationYmm": 10
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 30,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 87,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "07-P2 DIMM 7-12",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 4,
                    "LocationYmm": 4
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "08-HD Max",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 1,
                    "LocationYmm": 0
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "09-Chipset",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 7,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 44,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 105,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "10-Chipset Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 8,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 80,
            "UpperThresholdFatal": 85
        },
        {
            "Name": "11-P/S 1",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 12,
                    "LocationYmm": 1
                }
            },
            "PhysicalContext": "PowerSupply",
            "ReadingCelsius": 24,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "12-P/S 2",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 12,
                    "LocationYmm": 5
                }
            },
            "PhysicalContext": "PowerSupply",
            "ReadingCelsius": 26,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "13-P/S 3",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 12,
                    "LocationYmm": 9
                }
            },
            "PhysicalContext": "PowerSupply",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "14-P/S 4",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 12,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "PowerSupply",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "15-VR P1",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 7
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 37,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 115,
            "UpperThresholdFatal": 120
        },
        {
            "Name": "16-VR P2",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 0,
                    "LocationYmm": 8
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 36,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 115,
            "UpperThresholdFatal": 120
        },
        {
            "Name": "17-VR P1 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 7
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 28,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 90,
            "UpperThresholdFatal": 95
        },
        {
            "Name": "18-VR P2 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 0,
                    "LocationYmm": 8
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 90,
            "UpperThresholdFatal": 95
        },
        {
            "Name": "19-VR P1 Mem",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 10,
                    "LocationYmm": 12
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 30,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 115,
            "UpperThresholdFatal": 120
        },
        {
            "Name": "20-VR P1 Mem",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 10,
                    "LocationYmm": 2
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 34,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 115,
            "UpperThresholdFatal": 120
        },
        {
            "Name": "21-VR P2 Mem",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 2,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 31,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 115,
            "UpperThresholdFatal": 120
        },
        {
            "Name": "22-VR P2 Mem",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 1,
                    "LocationYmm": 3
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 30,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 115,
            "UpperThresholdFatal": 120
        },
        {
            "Name": "23-Supercap Max",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 0,
                    "LocationYmm": 0
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "24-HD Controller",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 4,
                    "LocationYmm": 1
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 40,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 100,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "25-iLO Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 10,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 23,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 80,
            "UpperThresholdFatal": 85
        },
        {
            "Name": "26-LOM",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 15,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "27-PCI 1",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 0
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "28-PCI 2",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 1
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "29-PCI 3",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 1
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "30-PCI 4",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 2
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "31-PCI 5",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 12
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "32-PCI 6",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 12
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "33-PCI 7",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "34-PCI 8",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 14
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "35-PCI 9",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 13,
                    "LocationYmm": 15
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 0,
            "Status": {
                "State": "Absent"
            },
            "UpperThresholdCritical": 0,
            "UpperThresholdFatal": 0
        },
        {
            "Name": "36-PCI 1 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 0
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "37-PCI 2 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 1
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "38-PCI 3 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 1
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 26,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "39-PCI 4 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 2
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 27,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "40-PCI 5 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 12
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 27,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "41-PCI 6 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 12
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 26,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "42-PCI 7 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 13
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "43-PCI 8 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 14
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 23,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "44-PCI 9 Zone",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 14,
                    "LocationYmm": 15
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 24,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 70,
            "UpperThresholdFatal": 75
        },
        {
            "Name": "45-P/S Board 1",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 7,
                    "LocationYmm": 2
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 57,
            "UpperThresholdFatal": 62
        },
        {
            "Name": "46-P/S Board 2",
            "Oem": {
                "Hp": {
                    "@odata.type": "#HpSeaOfSensors.1.0.0.HpSeaOfSensors",
                    "LocationXmm": 6,
                    "LocationYmm": 12
                }
            },
            "PhysicalContext": "SystemBoard",
            "ReadingCelsius": 25,
            "Status": {
                "Health": "OK",
                "State": "Enabled"
            },
            "UpperThresholdCritical": 57,
            "UpperThresholdFatal": 62
        }
    ]
}
