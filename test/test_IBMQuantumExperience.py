import sys
sys.path.append('../IBMQuantumExperience')
from IBMQuantumExperience import IBMQuantumExperience
import unittest
from config import *


class TestQX(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    """ ---------------------------------
            TESTS
        ---------------------------------
    """

    def test_api_auth_token(self):
        '''
        Authentication with Quantum Experience Platform
        '''
        api = IBMQuantumExperience(API_TOKEN)
        credential = api._check_credentials()
        self.assertTrue(credential)

    def test_api_last_codes(self):
        '''
        Check last code by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        self.assertIsNotNone(api.get_last_codes())

    def test_api_run_experiment(self):
        '''
        Check run an experiment by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        qasm = "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nu2(-4*pi/3,2*pi) q[0];\nu2(-3*pi/2,2*pi) q[0];\nu3(-pi,0,-pi) q[0];\nu3(-pi,0,-pi/2) q[0];\nu2(pi,-pi/2) q[0];\nu3(-pi,0,-pi/2) q[0];\nmeasure q -> c;\n"
        device = 'simulator'
        shots = 1
        experiment = api.run_experiment(qasm, device, shots)
        self.assertIsNotNone(experiment['status'])

    def test_api_run_experiment_with_seed(self):
        '''
        Check run an experiment with seed by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        qasm = "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nu2(-4*pi/3,2*pi) q[0];\nu2(-3*pi/2,2*pi) q[0];\nu3(-pi,0,-pi) q[0];\nu3(-pi,0,-pi/2) q[0];\nu2(pi,-pi/2) q[0];\nu3(-pi,0,-pi/2) q[0];\nmeasure q -> c;\n"
        device = 'simulator'
        shots = 1
        seed = 815
        experiment = api.run_experiment(qasm, device, shots, seed=seed)
        self.assertEqual(int(experiment['result']['extraInfo']['seed']), seed)

    def test_api_run_experiment_fail_device(self):
        '''
        Check run an experiment by user authenticated is not runned because the device is not exist
        '''
        api = IBMQuantumExperience(API_TOKEN)
        qasm = "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nu2(-4*pi/3,2*pi) q[0];\nu2(-3*pi/2,2*pi) q[0];\nu3(-pi,0,-pi) q[0];\nu3(-pi,0,-pi/2) q[0];\nu2(pi,-pi/2) q[0];\nu3(-pi,0,-pi/2) q[0];\nmeasure q -> c;\n"
        device = '5qreal'
        shots = 1
        experiment = api.run_experiment(qasm, device, shots)
        self.assertIsNotNone(experiment['error'])

    def test_api_run_job(self):
        '''
        Check run an job by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        qasm1 = { "qasm": "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nu2(-4*pi/3,2*pi) q[0];\nu2(-3*pi/2,2*pi) q[0];\nu3(-pi,0,-pi) q[0];\nu3(-pi,0,-pi/2) q[0];\nu2(pi,-pi/2) q[0];\nu3(-pi,0,-pi/2) q[0];\nmeasure q -> c;\n"}
        qasm2 = { "qasm": "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nx q[0];\nmeasure q -> c;\n"}
        qasms = [qasm1, qasm2]
        device = 'simulator'
        shots = 1
        job = api.run_job(qasms, device, shots)
        self.assertIsNotNone(job['status'])

    def test_api_run_job_fail_device(self):
        '''
        Check run an job by user authenticated is not runned because the device is not exist
        '''
        api = IBMQuantumExperience(API_TOKEN)
        qasm1 = { "qasm": "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nu2(-4*pi/3,2*pi) q[0];\nu2(-3*pi/2,2*pi) q[0];\nu3(-pi,0,-pi) q[0];\nu3(-pi,0,-pi/2) q[0];\nu2(pi,-pi/2) q[0];\nu3(-pi,0,-pi/2) q[0];\nmeasure q -> c;\n"}
        qasm2 = { "qasm": "IBMQASM 2.0;\n\ninclude \"qelib1.inc\";\nqreg q[5];\ncreg c[5];\nx q[0];\nmeasure q -> c;\n"}
        qasms = [qasm1, qasm2]
        device = 'real5'
        shots = 1
        job = api.run_job(qasms, device, shots)
        self.assertIsNotNone(job['error'])

    def test_api_device_status(self):
        '''
        Check the status of a real chip
        '''
        api = IBMQuantumExperience(API_TOKEN)
        is_available = api.device_status()
        self.assertIsNotNone(is_available)

    def test_api_device_calibration(self):
        '''
        Check the calibration of a real chip
        '''
        api = IBMQuantumExperience(API_TOKEN)
        calibration = api.device_calibration()
        self.assertIsNotNone(calibration)

    def test_api_device_parameters(self):
        '''
        Check the parameters of calibration of a real chip
        '''
        api = IBMQuantumExperience(API_TOKEN)
        parameters = api.device_parameters()
        self.assertIsNotNone(parameters)

    def test_api_devices_availables(self):
        '''
        Check the devices availables
        '''
        api = IBMQuantumExperience(API_TOKEN)
        devices = api.available_devices()
        self.assertGreaterEqual(len(devices), 2)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQX)
    unittest.TextTestRunner(verbosity=2).run(suite)
