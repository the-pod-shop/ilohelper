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
                self.avgtemp  = numpy.mean(temperatures)
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

