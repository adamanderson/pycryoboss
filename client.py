import socket
import time

class CryobossClient(object):
    '''
    Python client object for interacting with cryoboss ADR control software
    from HPD.
    '''
    def __init__(self, ip, port, voltage_divider=False):
        '''
        Constructor.

        Parameters
        ----------
        ip : string
            IP address of computer running cryoboss
        port : int
            Port that cryoboss is listening to
        voltage_divider : bool
            Set to true if the voltage divider is installed in the ADR control
            electronics to enable higher-temperature control
        '''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.voltage_divider = voltage_divider


    def get_data(self):
        '''
        Get temperature and magnet data from cryoboss.

        Returns
        -------
        data_dict : dict
            Dictionary of data
        '''
        # get and unpack the data
        self.socket.send(b'queryall')
        data = self.socket.recvfrom(2048)
        data = data[0].decode("utf-8").split(',')
        data = data[:20]
        self.socket.send(b'queryheader')
        header = self.socket.recvfrom(2048)
        header_temp = header[0].decode("utf-8").split('\r\n')
        header = [h.split(',')[0] for h in header_temp]
        header = header[1:21]

        data_dict = {}
        for h, d in zip(header,data):
            
            try:
                data_dict[h] = float(d)
            except:
                data_dict[h] = d

        return data_dict


    def set_pid(self, setpoint):
        '''
        Set the FAA PID setpoint. Because of safety checks built in to this
        function, the execution time is 10 sec.

        Parameters
        ----------
        setpoint : float
            Temperature setpoint in Kelvin

        Returns
        -------
        result : str
            Acknowledgement string from cryoboss
        '''
        # check voltage divider
        if self.voltage_divider is False and setpoint > 0.15:
            raise ValueError('Cannot regulate above 0.15 K without voltage '
                             'divider installed.')
        
        # do not allow setpoint to be increased more than 20mK above the
        # current FAA temperature
        data = self.get_data()
        if setpoint > data['50 mK FAA Temperature'] + 0.020:
            raise ValueError('Cannot set FAA setpoint more than 20mK above '
                             'the current FAA temperature.')

        # do not allow setpoint to be increased if Kepco voltage is > 14V or
        # current is > 8A
        if (setpoint > data['PID Setpoint']) and (data['Magnet Current'] > 8):
            raise ValueError('Magnet current is {:4f} A. Cannot increase '
                             'setpoint when current exceeds 8 A.'\
                                 .format(data['Magnet Current']))
        if (setpoint > data['PID Setpoint']) and (data['Power Supply Voltage'] > 14):
            raise ValueError('Power supply voltage is {:4f} V. Cannot increase '
                             'setpoint when current exceeds 14 V.'\
                                 .format(data['Power Supply Voltage']))

        # do not allow the setpoint to be increased if FAA temperature is
        # increasing faster than 1mK / 10s
        time.sleep(10)
        data_new = self.get_data()
        delta_T = data_new['50 mK FAA Temperature'] - data['50 mK FAA Temperature']
        if (setpoint > data_new['PID Setpoint']) and (delta_T > 0.001):
            raise ValueError('FAA temperature increased {:4f} K in 10 sec. '
                             'Cannot increase FAA setpoint when the rate is '
                             '>0.001 K per 10 sec.'.format(delta_T))
        
        # now actually change the setpoint
        self.socket.send('pidset = {:4f}'.format(setpoint).encode('utf_8'))
        result = self.socket.recvfrom(2048)
        return result
