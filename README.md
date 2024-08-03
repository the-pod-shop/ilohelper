# ilohelper
a little python wrapper class for the [ilo restful api](https://hewlettpackard.github.io/python-ilorest-library/index.html)


## Installation

Requires Python and the `redfish` library. Install it using:
  ```bash
  pip install redfish
  ```
## Commands
| Description | Method | Command |
|---|---|---|
| Get temperature data | client.get_temperatures() | temperatures |
| Get server status | client.get_server_status() | serverStatus |
| Start the server | client.start_server() | startServer |
| Stop the server | client.stop_server() | stopServer |
| Wait until the server boots up | client.waitForBoot() | waitForBoot |





## Usage
- via cli:
  ```bash
  $ python login.py <COMMAND> <ILO-IP> <ILO-USER> <ILO-PASSWORD> (<SERVER-IP>)
  ```
- via script:
  ```python
     client = ilohelper(<COMMAND> <ILO-IP> <ILO-USER> <ILO-PASSWORD> (<SERVER-IP>)
  ```
--- 

### Examples

- get the status and create your ilohelper object:
  ```bash
  $ python ./ilohelper.py serverStatus 192.168.200.11 Administrator AGSBTGWW 
  ```

  - output:
     ```python
      sensor42-PCI 7 Zone has 25 degrees
      sensor43-PCI 8 Zone has 23 degrees
      sensor44-PCI 9 Zone has 24 degrees
      sensor45-P/S Board 1 has 25 degrees
      sensor46-P/S Board 2 has 25 degrees
      mintemp 0
      maxtemp 44
      avg 19.565217391304348
      power: Off
      memory: 96
      cpu: 
      {'Count': 2, 'Model': ' Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz      ', 'Status': {'HealthRollup': 'OK'}}
    ```
- start the server and wait untill its booted up:
  ```bash
  $ python ./utils/ilo/login.py waitForBoot 192.168.200.11 Administrator AGSBTGWW 192.168.200.12
  ```
  - output:
    ```bash
       ...
        Content-type application/json; charset=utf-8
        Date Sat, 03 Aug 2024 08:55:11 GMT
        ETag W/"C84E3EA9"
        OData-Version 4.0
        X-Content-Type-Options nosniff
        X-Frame-Options sameorigin
        X-XSS-Protection 1; mode=block
        X_HP-CHRP-Service-Version 1.0.3
        
        
        {"error":{"@Message.ExtendedInfo":[{"MessageId":"Base.0.10.Success"}],"code":"iLO.0.10.ExtendedInfo","message":"See @Message.ExtendedInfo for more information."}}
        
        waiting till turned on
        ....waiting 5 seconds
        CompletedProcess(args=['ping', '-c', '1', '192.168.200.12'], returncode=1, stdout='PING 192.168.200.12 (192.168.200.12) 56(84) bytes of data.\n\n--- 192.168.200.12 ping statistics ---\n1 Pakete übertragen, 0 empfangen, 100% packet loss, time 0ms\n\n')
        server has bootet
        finished after 1 seconds
     ```
- get the temperatures:
  - this function returns an array of all temperatures
  - it will also update the Mintemp, Maxtemp and Avgtemp values.
  ```bash
  $ python ./ilohelper.py serverStatus 192.168.200.11 Administrator AGSBTGWW  
  ```
  - output:
    ```bash
      ...
      Sensor 43-PCI 8 Zone has 23 degrees
      Sensor 44-PCI 9 Zone has 25 degrees
      Sensor 45-P/S Board 1 has 27 degrees
      Sensor 46-P/S Board 2 has 27 degrees
      Mintemp: 0
      Maxtemp: 47
      Avgtemp: 20.41304347826087
      will return: 
      [21, 47, 40, 30, 34, 28, 0, 0, 44, 25, 25, 30, 0, 0, 44, 36, 33, 24, 30, 34, 31, 30, 0, 40, 23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 26, 26, 27, 28, 28, 27, 26, 23, 25, 27, 27]
    ``` 
    ---
  - note that this script loggs you out of the session when the object gets destroyed.
    - you can keep the object alive in a loop, so it doesnt take to long to repeat request 
