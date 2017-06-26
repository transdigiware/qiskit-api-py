'''
    IBM Quantum Experience Python API Client
'''
import json
import time
import requests
from datetime import datetime


class _Credentials(object):

    config_base = {'url': 'https://quantumexperience.ng.bluemix.net/api'}

    def __init__(self, token, config=None):
        self.token_unique = token
        if config and config.get('url', None):
            self.config = config
        else:
            self.config = self.config_base

        self.data_credentials = {}
        self.obtain_token()

    def obtain_token(self):
        '''
        Obtain the token to access to QX Platform
        '''
        self.data_credentials = requests.post(str(self.config.get('url') +
                                                  "/users/loginWithToken"),
                                              data={'apiToken':
                                                    self.token_unique}).json()

        if not self.get_token():
            print('ERROR: Not token valid')

    def get_token(self):
        '''
        Get Authenticated Token to connect with QX Platform
        '''
        return self.data_credentials.get('id', None)

    def get_user_id(self):
        '''
        Get User Id in QX Platform
        '''
        return self.data_credentials.get('userId', None)

    def get_config(self):
        '''
        Get Configuration setted to connect with QX Platform
        '''
        return self.config


class _Request(object):

    def __init__(self, token, config=None):
        self.credential = _Credentials(token, config)

    def check_token(self, respond):
        '''
        Check is the user's token is valid
        '''
        if respond.status_code == 401:
            self.credential.obtain_token()
            return False
        return True

    def post(self, path, params='', data=None):
        '''
        POST Method Wrapper of the REST API
        '''
        data = data or {}
        headers = {'Content-Type': 'application/json'}
        url = str(self.credential.config['url'] + path + '?access_token=' +
                  self.credential.get_token() + params)
        respond = requests.post(url, data=data, headers=headers)
        if not self.check_token(respond):
            respond = requests.post(url, data=data, headers=headers)
        return respond.json()

    def get(self, path, params='', with_token=True):
        '''
        GET Method Wrapper of the REST API
        '''
        access_token = ''
        if with_token:
            access_token = self.credential.get_token() or ''
            if access_token:
                access_token = '?access_token=' + str(access_token)
        url = self.credential.config['url'] + path + access_token + params
        respond = requests.get(url)
        if not self.check_token(respond):
            respond = requests.get(url)
        return respond.json()


class IBMQuantumExperience(object):
    '''
    The Connector Class to do request to QX Platform
    '''
    __names_device_ibmqxv2 = ['ibmqx5qv2', 'ibmqx2', 'qx5qv2', 'qx5q', 'real']
    __names_device_ibmqxv3 = ['ibmqx3']
    __names_device_simulator = ['simulator', 'sim_trivial_2',
                                'ibmqx_qasm_simulator']

    def __init__(self, token, config=None):
        self.req = _Request(token, config)

    def _check_device(self, device, endpoint):
        '''
        Check if the name of a device is valid to run in QX Platform
        '''
        device = device.lower()
        if endpoint == 'experiment':
            if device in self.__names_device_ibmqxv2:
                return 'real'
            elif device in self.__names_device_ibmqxv3:
                return 'ibmqx3'
            elif device in self.__names_device_simulator:
                return 'sim_trivial_2'
        elif endpoint == 'job':
            if device in self.__names_device_ibmqxv2:
                return 'real'
            elif device in self.__names_device_ibmqxv3:
                return 'ibmqx3'
            elif device in self.__names_device_simulator:
                return 'simulator'
        elif endpoint == 'status':
            if device in self.__names_device_ibmqxv2:
                return 'chip_real'
            elif device in self.__names_device_ibmqxv3:
                return 'ibmqx3'
            elif device in self.__names_device_simulator:
                return 'chip_simulator'
        elif endpoint == 'calibration':
            if device in self.__names_device_ibmqxv2:
                return 'ibmqx2'
            elif device in self.__names_device_ibmqxv3:
                return 'ibmqx3'
        return None

    def check_credentials(self):
        '''
        Check if the user has permission in QX platform
        '''
        return bool(self.req.credential.get_token())

    def get_execution(self, id_execution):
        '''
        Get a execution, by its id
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        execution = self.req.get('/Executions/' + id_execution)
        if execution["codeId"]:
            execution['code'] = self.get_code(execution["codeId"])
        return execution

    def get_result_from_execution(self, id_execution):
        '''
        Get the result of a execution, byt the execution id
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        execution = self.req.get('/Executions/' + id_execution)
        result = {}
        if "result" in execution and "data" in execution["result"]:
            if execution["result"]["data"].get('p', None):
                result["measure"] = execution["result"]["data"]["p"]
            if execution["result"]["data"].get('valsxyz', None):
                result["bloch"] = execution["result"]["data"]["valsxyz"]
            if "additionalData" in execution["result"]["data"]:
                result["extraInfo"] = execution["result"]["data"]["additionalData"]

        return result

    def get_code(self, id_code):
        '''
        Get a code, by its id
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        code = self.req.get('/Codes/' + id_code)
        executions = self.req.get('/Codes/' + id_code + '/executions',
                                  '&filter={"limit":3}')
        if isinstance(executions, list):
            code["executions"] = executions
        return code

    def get_image_code(self, id_code):
        '''
        Get the image of a code, by its id
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        return self.req.get('/Codes/' + id_code + '/export/png/url')

    def get_last_codes(self):
        '''
        Get the last codes of the user
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        last = '/users/' + self.req.credential.get_user_id() + '/codes/lastest'
        return self.req.get(last, '&includeExecutions=true')['codes']

    def run_experiment(self, qasm, device='simulator', shots=1, name=None,
                       seed=None, timeout=60):
        '''
        Execute an experiment
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}

        device_type = self._check_device(device, 'experiment')
        if not device_type:
            fmt = ("Device {} not exits in Quantum Experience. Only allow "
                   "ibmqx2, ibmqx3 or simulator")
            return {"error": fmt.format(device)}

        if device not in self.__names_device_simulator and seed:
            return {"error": "Not seed allowed in " + device}

        name = name or 'Experiment #{:%Y%m%d%H%M%S}'.format(datetime.now())
        qasm = qasm.replace('IBMQASM 2.0;', '').replace('OPENQASM 2.0;', '')
        data = json.dumps({'qasm': qasm, 'codeType': 'QASM2', 'name': name})

        if seed and len(str(seed)) < 11 and str(seed).isdigit():
            params = '&shots={}&seed={}&deviceRunType={}'.format(shots, seed,
                                                                 device_type)
            execution = self.req.post('/codes/execute', params, data)
        elif seed:
            return {"error": "Not seed allowed. Max 10 digits."}
        else:
            params = '&shots={}&deviceRunType={}'.format(shots, device_type)
            execution = self.req.post('/codes/execute', params, data)
        respond = {}
        try:
            status = execution["status"]["id"]
            id_execution = execution["id"]
            result = {}
            respond["status"] = status
            respond["idExecution"] = id_execution
            respond["idCode"] = execution["codeId"]

            if 'infoQueue' in execution:
                respond['infoQueue'] = execution['infoQueue']

            if status == "DONE":
                if "result" in execution and "data" in execution["result"]:
                    if "additionalData" in execution["result"]["data"]:
                        result["extraInfo"] = execution["result"]["data"]["additionalData"]
                    if execution["result"]["data"].get('p', None):
                        result["measure"] = execution["result"]["data"]["p"]
                    if execution["result"]["data"].get('valsxyz', None):
                        result["bloch"] = execution["result"]["data"]["valsxyz"]
                    respond["result"] = result
                    respond.pop('infoQueue', None)

                    return respond
            elif status == "ERROR":
                respond.pop('infoQueue', None)
                return respond
            else:
                if timeout:
                    for _ in range(1, timeout):
                        print("Waiting for results...")
                        result = self.get_result_from_execution(id_execution)
                        if result:
                            respond["status"] = 'DONE'
                            respond["result"] = result
                            respond.pop('infoQueue', None)
                            return respond
                        else:
                            time.sleep(2)
                    return respond
                else:
                    return respond
        except Exception:
            respond["error"] = execution
            return respond

    def run_job(self, qasms, device='simulator', shots=1,
                max_credits=3, seed=None):
        '''
        Execute a job
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        for qasm in qasms:
            qasm['qasm'] = qasm['qasm'].replace('IBMQASM 2.0;', '')
            qasm['qasm'] = qasm['qasm'].replace('OPENQASM 2.0;', '')
        data = {'qasms': qasms,
                'shots': shots,
                'maxCredits': max_credits,
                'backend': {}}

        device_type = self._check_device(device, 'job')

        if not device_type:
            fmt = ("Device {} not exits in Quantum Experience. Only allow "
                   "ibmqx2, ibmqx3 or simulator")
            return {"error": fmt.format(device)}
        if device not in self.__names_device_simulator and seed:
            return {"error": "Not seed allowed in " + device}

        if seed and len(str(seed)) < 11 and str(seed).isdigit():
            data['seed'] = seed
        elif seed:
            return {"error": "Not seed allowed. Max 10 digits."}

        data['backend']['name'] = device_type

        job = self.req.post('/Jobs', data=json.dumps(data))
        return job

    def get_job(self, id_job):
        '''
        Get the information about a job, by its id
        '''
        if not self.check_credentials() or not id_job:
            return {"error": "Not credentials valid"}
        job = self.req.get('/Jobs/' + id_job)
        return job

    def get_jobs(self, limit=50):
        '''
        Get the information about the user jobs
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        jobs = self.req.get('/Jobs', '&filter={"limit":' + str(limit) + '}')
        return jobs

    def device_status(self, device='ibmqx2'):
        '''
        Get the status of a chip
        '''
        device_type = self._check_device(device, 'status')
        if not device_type:
            fmt = ("Device {} not exits in Quantum Experience. Only allow "
                   "ibmqx2, ibmqx3 or simulator")
            return {"error": fmt.format(device)}

        status = self.req.get('/Status/queue?device=' + device_type,
                              with_token=False)["state"]
        return {'available': bool(status)}

    def device_calibration(self, device='ibmqx2'):
        '''
        Get the calibration of a real chip
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}

        device_type = self._check_device(device, 'calibration')

        if not device_type:
            fmt = ("Device {} not exits in Quantum Experience Real Devices. "
                   "Only allow ibmqx2, ibmqx3 or simulator")
            return {"error": fmt.format(device)}

        ret = self.req.get('/Backends/' + device_type + '/calibration')
        ret["device"] = device_type
        return ret

    def device_parameters(self, device='ibmqx2'):
        '''
        Get the parameters of calibration of a real chip
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}

        device_type = self._check_device(device, 'calibration')

        if not device_type:
            fmt = ("Device {} not exits in Quantum Experience Real Devices. "
                   "Only allow ibmqx2, ibmqx3 or simulator")
            return {"error": fmt.format(device)}

        ret = self.req.get('/Backends/' + device_type + '/parameters')
        ret["device"] = device_type
        return ret

    def available_devices(self):
        '''
        Get the devices availables to use in the QX Platform
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        else:
            return [device for device in self.req.get('/Backends')
                    if device.get('status') == 'on']
