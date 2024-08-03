# ilohelper
a little python wrapper class for the [ilo restful api](https://hewlettpackard.github.io/python-ilorest-library/index.html)
- install redfish:
  ```bash
  pip install redfish
  ```
- get the status and create your ilohelper object:
  ```bash
  python ./ilohelper.py <ilo ip/domain> <ilo user> <your ilo pass>
  ```
  - respose:
     ```python
      sensor42-PCI 7 Zone has 25 degrees
      sensor43-PCI 8 Zone has 23 degrees
      sensor44-PCI 9 Zone has 24 degrees
      sensor45-P/S Board 1 has 25 degrees
      sensor46-P/S Board 2 has 25 degrees
      mintemp 0
      maxtemp 44
      avg 19.565217391304348
      powerOff
      memory: 96
      cpu: 
      {'Count': 2, 'Model': ' Intel(R) Xeon(R) CPU E5-2680 v2 @ 2.80GHz      ', 'Status': {'HealthRollup': 'OK'}}
    ```
- note that this script loggs you out of the session when the object gets destroyed.
  - you can keep the object alive in a loop, so it doesnt take to long to repeat request 
