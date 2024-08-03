# ilohelper
a little python wrapper class and cli tool for the [ilo restful api](https://hewlettpackard.github.io/python-ilorest-library/index.html)
- You can, Start, Stop the server and get Server Status, or temperature information
- ***🚀 start you server and wait untill the boot process finishes using a single command 🚀***
  - use it in ansible, or in any other cicd tool to for automated ssh connections
- All Commands can also get executed using the cli.
- The ilohelper-object creates a session for you and logs you out when the object gets destroyed
  - you can keep the object alive in a loop, so it doesnt take to long to repeat requests
    
## Installation

Requires Python and the `redfish` library. Install it using:
  ```bash
  $ pip install redfish
  ```


## Usage

- via cli:
  ```bash
  $ python login.py <COMMAND> <ILO-IP> <ILO-USER> <ILO-PASSWORD> (<SERVER-IP>)
  ```
- via script:
  ```python
  $ client = ilohelper(<COMMAND> <ILO-IP> <ILO-USER> <ILO-PASSWORD> (<SERVER-IP>)
  ```
- ***note that waitForBoot requires the optional server-ip argument for the ping command in the subprocess***
--- 


## Commands & Variables



<table>
    <tr>
        <th>Commands</th>
        <th>ilohelper Class Variables</th>
    </tr>
    <tr>
        <td>
            <table>
                <tr>
                    <th>Description</th>
                    <th>Method</th>
                    <th>Command</th>
                </tr>
                <tr>
                    <td>Get temperature data</td>
                    <td>ilohelper.get_temperatures()</td>
                    <td>temperatures</td>
                </tr>
                <tr>
                    <td>Get server status</td>
                    <td>ilohelper.get_server_status()</td>
                    <td>serverStatus</td>
                </tr>
                <tr>
                    <td>Start the server</td>
                    <td>ilohelper.start_server()</td>
                    <td>startServer</td>
                </tr>
                <tr>
                    <td>Stop the server</td>
                    <td>ilohelper.stop_server()</td>
                    <td>stopServer</td>
                </tr>
                <tr>
                    <td>Wait until the server boots up</td>
                    <td>ilohelper.waitForBoot()</td>
                    <td>waitForBoot</td>
                </tr>
            </table>
        </td>
        <td>
            <table>
                <tr>
                    <th>Variable</th>
                    <th>Description</th>
                    <th>Type</th>
                </tr>
                <tr>
                    <td>target_ip</td>
                    <td>server ip</td>
                    <td>str</td>
                </tr>
                <tr>
                    <td>iLO_host</td>
                    <td>ilo ip</td>
                    <td>str</td>
                </tr>
                <tr>
                    <td>login_account</td>
                    <td>ilo user account</td>
                    <td>str</td>
                </tr>
                <tr>
                    <td>login_password</td>
                    <td>ilo user password</td>
                    <td>str</td>
                </tr>
                <tr>
                    <td>mintemp</td>
                    <td>lowest temperature</td>
                    <td>int</td>
                </tr>
                <tr>
                    <td>maxtemp</td>
                    <td>highest temperature</td>
                    <td>int</td>
                </tr>
                <tr>
                    <td>avgtemp</td>
                    <td>average temperature</td>
                    <td>float</td>
                </tr>
                <tr>
                    <td>power_state</td>
                    <td>server power status</td>
                    <td>bool</td>
                </tr>
                <tr>
                    <td>memory</td>
                    <td>memory in GB</td>
                    <td>int</td>
                </tr>
                <tr>
                    <td>cpu</td>
                    <td>cpu object</td>
                    <td>dict</td>
                </tr>
            </table>
        </td>
    </tr>
</table>



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
  - this will also 
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

