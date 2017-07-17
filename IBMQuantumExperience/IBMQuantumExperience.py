'''
    IBM Quantum Experience Python API Client
'''
import json
import time
import logging
from datetime import datetime
import sys
import traceback
import requests


class IBMQuantumExperienceApiError(Exception):
    '''
    IBMQuantumExperience API error handling base class.
    '''
    def __init__(self, usr_msg=None, dev_msg=None):
        '''
        Parameters
        ----------
        usr_msg : str or None, optional
           Short user facing message describing error.
        dev_msg : str or None, optional
           More detailed message to assist developer with resolving issue.
        '''
        Exception.__init__(self, usr_msg)
        self.usr_msg = usr_msg
        self.dev_msg = dev_msg

    def __repr__(self):
        return repr(self.dev_msg)

    def __str__(self):
        return str(self.usr_msg)


class BadBackendError(IBMQuantumExperienceApiError):
    '''
    Unavailable backend error.
    '''
    def __init__(self, backend):
        '''
        Parameters
        ----------
        backend : str
           Name of backend.
        '''
        usr_msg = ('Could not find backend "{0}" available.').format(backend)
        dev_msg = ('Backend "{0}" does not exist. Please use '
                   'available_backends to see options').format(backend)
        IBMQuantumExperienceApiError.__init__(self, usr_msg=usr_msg,
                                              dev_msg=dev_msg)


class _Credentials(object):
    '''
    The Credential class to manage the tokens
    '''
    config_base = {'url': 'https://quantumexperience.ng.bluemix.net/api'}

    def __init__(self, token, config=None, verify=True):
        self.token_unique = token
        self.verify = verify
        if not verify:
            import requests.packages.urllib3 as urllib3
            urllib3.disable_warnings()
            print('-- Ignoring SSL errors.  This is not recommended --')
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
                                                    self.token_unique},
                                              verify=self.verify).json()

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
    '''
    The Request class to manage the methods
    '''
    def __init__(self, token, config=None, verify=True, retries=5,
                 timeout_interval=1.0):
        self.verify = verify
        self.credential = _Credentials(token, config, verify)
        self.log = logging.getLogger(__name__)
        if not isinstance(retries, int):
            raise TypeError('post retries must be positive integer')
        self.retries = retries
        self.timeout_interval = timeout_interval
        self.result = None

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
        retries = self.retries
        while retries > 0:
            respond = requests.post(url, data=data, headers=headers,
                                    verify=self.verify)
            if not self.check_token(respond):
                respond = requests.post(url, data=data, headers=headers,
                                        verify=self.verify)
            if self._response_good(respond):
                return self.result
            else:
                retries -= 1
                time.sleep(self.timeout_interval)
        # timed out
        raise IBMQuantumExperienceApiError(usr_msg='Failed to get proper ' +
                                           'response from backend.')

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
        retries = self.retries
        while retries > 0: # Repeat until no error
            respond = requests.get(url, verify=self.verify)
            if not self.check_token(respond):
                respond = requests.get(url, verify=self.verify)
            if self._response_good(respond):
                return self.result
            else:
                retries -= 1
                time.sleep(self.timeout_interval)
        # timed out
        raise IBMQuantumExperienceApiError(usr_msg='Failed to get proper ' +
                                           'response from backend.')

    def _response_good(self, respond):
        '''
        check response

        Parameters
        ----------
        respond : str
           HTTP response.

        Returns
        -------
        bool
           True if the response is good, else False.

        Raises
        ------
        Raises IBMQuantumExperienceApiError if response isn't formatted
        properly.
        '''
        if respond.status_code == 400:
            self.log.warning("Got a 400 code response to %s", respond.url)
            return False
        try:
            self.result = respond.json()
        except Exception:
            usr_msg = ('JSON conversion failed: url: {0}, status: {1},'
                       'reason: {2}, text: {3}')
            exc_type, exc_value, exc_traceback = None, None, None
            try:
                exc_type, exc_value, exc_traceback = sys.exc_info()
            except:
                raise
            else:
                err_list = traceback.format_exception(exc_type, exc_value,
                                                      exc_traceback)
                err_list = err_list[-2:]
                module_info = err_list[0].split(',')
                module_name = module_info[0].split('/')[-1].rstrip('"').split('.')[0]
                module_line = module_info[1].lstrip()
                dev_msg = '{0} {1} {2}'.format(module_name, module_line,
                                               err_list[1])
            finally:
                # may not be necessary in python3 but should be safe and maybe
                # avoid need to garbage collect cycle?
                del exc_type, exc_value, exc_traceback

            raise IBMQuantumExperienceApiError(
                usr_msg=usr_msg.format(respond.url, respond.status_code,
                                       respond.reason, respond.text),
                dev_msg=dev_msg)
        else:
            if not isinstance(self.result, (list, dict)):
                msg = ('JSON not a list or dict: url: {0},'
                       'status: {1}, reason: {2}, text: {3}')
                raise IBMQuantumExperienceApiError(
                    usr_msg=msg.format(respond.url,
                                       respond.status_code,
                                       respond.reason, respond.text))
        if ('error' not in self.result or
                ('status' not in self.result['error'] or
                 self.result['error']['status'] != 400)):
            return True
        else:
            self.log.warning("Got a 400 code JSON response to %s", respond.url)
            return False


class IBMQuantumExperience(object):
    '''
    The Connector Class to do request to QX Platform
    '''
    __names_backend_ibmqxv2 = ['ibmqx5qv2', 'ibmqx2', 'qx5qv2', 'qx5q', 'real']
    __names_backend_ibmqxv3 = ['ibmqx3']
    __names_backend_simulator = ['simulator', 'sim_trivial_2',
                                 'ibmqx_qasm_simulator']

    def __init__(self, token, config=None, verify=True):
        ''' If verify is set to false, ignore SSL certificate errors '''
        self.req = _Request(token, config, verify)

    def _check_backend(self, backend, endpoint):
        '''
        Check if the name of a backend is valid to run in QX Platform
        '''
        # First check against hacks for old backend names
        original_backend = backend
        backend = backend.lower()
        if endpoint == 'experiment':
            if backend in self.__names_backend_ibmqxv2:
                return 'real'
            elif backend in self.__names_backend_ibmqxv3:
                return 'ibmqx3'
            elif backend in self.__names_backend_simulator:
                return 'sim_trivial_2'
        elif endpoint == 'job':
            if backend in self.__names_backend_ibmqxv2:
                return 'ibmqx2'
            elif backend in self.__names_backend_ibmqxv3:
                return 'ibmqx3'
            elif backend in self.__names_backend_simulator:
                return 'simulator'
        elif endpoint == 'status':
            if backend in self.__names_backend_ibmqxv2:
                return 'chip_real'
            elif backend in self.__names_backend_ibmqxv3:
                return 'ibmqx3'
            elif backend in self.__names_backend_simulator:
                return 'chip_simulator'
        elif endpoint == 'calibration':
            if backend in self.__names_backend_ibmqxv2:
                return 'ibmqx2'
            elif backend in self.__names_backend_ibmqxv3:
                return 'ibmqx3'

        # Check for new-style backends
        backends = self.available_backends()
        for backend in backends:
            if backend['name'] == original_backend:
                if backend.get('simulator', False):
                    return 'chip_simulator'
                else:
                    return original_backend
        # backend unrecognized
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
                ad_aux = execution["result"]["data"]["additionalData"]
                result["extraInfo"] = ad_aux
            if "calibration" in execution:
                result["calibration"] = execution["calibration"]

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

    def run_experiment(self, qasm, backend='simulator', shots=1, name=None,
                       seed=None, timeout=60):
        '''
        Execute an experiment
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}

        backend_type = self._check_backend(backend, 'experiment')
        if not backend_type:
            raise BadBackendError(backend)

        if backend not in self.__names_backend_simulator and seed:
            return {"error": "Not seed allowed in " + backend}

        name = name or 'Experiment #{:%Y%m%d%H%M%S}'.format(datetime.now())
        qasm = qasm.replace('IBMQASM 2.0;', '').replace('OPENQASM 2.0;', '')
        data = json.dumps({'qasm': qasm, 'codeType': 'QASM2', 'name': name})

        if seed and len(str(seed)) < 11 and str(seed).isdigit():
            params = '&shots={}&seed={}&deviceRunType={}'.format(shots, seed,
                                                                 backend_type)
            execution = self.req.post('/codes/execute', params, data)
        elif seed:
            return {"error": "Not seed allowed. Max 10 digits."}
        else:
            params = '&shots={}&deviceRunType={}'.format(shots, backend_type)
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
                        ad_aux = execution["result"]["data"]["additionalData"]
                        result["extraInfo"] = ad_aux
                    if execution["result"]["data"].get('p', None):
                        result["measure"] = execution["result"]["data"]["p"]
                    if execution["result"]["data"].get('valsxyz', None):
                        valsxyz = execution["result"]["data"]["valsxyz"]
                        result["bloch"] = valsxyz
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
                            respond["calibration"] = result["calibration"]
                            del result["calibration"]
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

    def run_job(self, qasms, backend='simulator', shots=1,
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

        backend_type = self._check_backend(backend, 'job')

        if not backend_type:
            raise BadBackendError(backend)

        if seed and len(str(seed)) < 11 and str(seed).isdigit():
            data['seed'] = seed
        elif seed:
            return {"error": "Not seed allowed. Max 10 digits."}

        data['backend']['name'] = backend_type

        job = self.req.post('/Jobs', data=json.dumps(data))
        return job

    def get_job(self, id_job):
        '''
        Get the information about a job, by its id
        '''
        if not self.check_credentials():
            respond = {}
            respond["status"] = 'Error'
            respond["error"] = "Not credentials valid"
            return respond
        if not id_job:
            respond = {}
            respond["status"] = 'Error'
            respond["error"] = "Job ID not specified"
            return respond
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

    def backend_status(self, backend='ibmqx2'):
        '''
        Get the status of a chip
        '''
        backend_type = self._check_backend(backend, 'status')
        if not backend_type:
            raise BadBackendError(backend)

        status = self.req.get('/Status/queue?backend=' + backend_type,
                              with_token=False)["state"]
        return {'available': bool(status)}

    def backend_calibration(self, backend='ibmqx2'):
        '''
        Get the calibration of a real chip
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}

        backend_type = self._check_backend(backend, 'calibration')

        if not backend_type:
            raise BadBackendError(backend)

        ret = self.req.get('/Backends/' + backend_type + '/calibration')
        ret["backend"] = backend_type
        return ret

    def backend_parameters(self, backend='ibmqx2'):
        '''
        Get the parameters of calibration of a real chip
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}

        backend_type = self._check_backend(backend, 'calibration')

        if not backend_type:
            raise BadBackendError(backend)

        ret = self.req.get('/Backends/' + backend_type + '/parameters')
        ret["backend"] = backend_type
        return ret

    def available_backends(self):
        '''
        Get the backends available to use in the QX Platform
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        else:
            return [backend for backend in self.req.get('/Backends')
                    if backend.get('status') == 'on']

    def available_backend_simulators(self):
        '''
        Get the backend simulators available to use in the QX Platform
        '''
        if not self.check_credentials():
            return {"error": "Not credentials valid"}
        else:
            return [backend for backend in self.req.get('/Backends')
                    if backend.get('status') == 'on' and
                    backend.get('simulator') is True]
