# pylint: disable=C0103
'''
Unit Test
'''

import sys
import unittest
# pylint: disable=W0403
from config import API_TOKEN
sys.path.append('IBMQuantumExperience')
sys.path.append('../IBMQuantumExperience')
# pylint: disable=C0413
if sys.version_info.major > 2:  # Python 3
    from IBMQuantumExperience.IBMQuantumExperience import IBMQuantumExperience  # noqa
else:  # Python 2
    from IBMQuantumExperience import IBMQuantumExperience  # noqa

from IBMQuantumExperience.IBMQuantumExperience import BadBackendError  # noqa

qasm = """IBMQASM 2.0;

include "qelib1.inc";
qreg q[5];
creg c[5];
u2(-4*pi/3,2*pi) q[0];
u2(-3*pi/2,2*pi) q[0];
u3(-pi,0,-pi) q[0];
u3(-pi,0,-pi/2) q[0];
u2(pi,-pi/2) q[0];
u3(-pi,0,-pi/2) q[0];
measure q -> c;
"""

qasms = [{"qasm": qasm},
         {"qasm": """IBMQASM 2.0;

include "qelib1.inc";
qreg q[5];
creg c[5];
x q[0];
measure q -> c;
"""}]


class TestQX(unittest.TestCase):
    '''
    Class with the unit tests
    '''

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
        credential = api.check_credentials()
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
        backend = api.available_backend_simulators()[0]['name']
        shots = 1
        experiment = api.run_experiment(qasm, backend, shots)
        self.assertIsNotNone(experiment['status'])

    def test_api_run_experiment_with_seed(self):
        '''
        Check run an experiment with seed by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        backend = api.available_backend_simulators()[0]['name']
        shots = 1
        seed = 815
        experiment = api.run_experiment(qasm, backend, shots, seed=seed)
        self.assertEqual(int(experiment['result']['extraInfo']['seed']), seed)

    def test_api_run_experiment_fail_backend(self):
        '''
        Check run an experiment by user authenticated is not run because the
        backend does not exist
        '''
        api = IBMQuantumExperience(API_TOKEN)
        backend = '5qreal'
        shots = 1
        self.assertRaises(BadBackendError,
                          api.run_experiment, qasm, backend, shots)

    def test_api_run_job(self):
        '''
        Check run an job by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        backend = 'simulator'
        shots = 1
        job = api.run_job(qasms, backend, shots)
        self.assertIsNotNone(job['status'])

    def test_api_run_job_fail_backend(self):
        '''
        Check run an job by user authenticated is not run because the backend
        does not exist
        '''
        api = IBMQuantumExperience(API_TOKEN)
        backend = 'real5'
        shots = 1
        self.assertRaises(BadBackendError, api.run_job, qasms, backend, shots)

    def test_api_get_jobs(self):
        '''
        Check get jobs by user authenticated
        '''
        api = IBMQuantumExperience(API_TOKEN)
        jobs = api.get_jobs(2)
        self.assertEqual(len(jobs), 2)

    def test_api_backend_status(self):
        '''
        Check the status of a real chip
        '''
        api = IBMQuantumExperience(API_TOKEN)
        is_available = api.backend_status()
        self.assertIsNotNone(is_available)

    def test_api_backend_calibration(self):
        '''
        Check the calibration of a real chip
        '''
        api = IBMQuantumExperience(API_TOKEN)
        calibration = api.backend_calibration()
        self.assertIsNotNone(calibration)

    def test_api_backend_parameters(self):
        '''
        Check the parameters of calibration of a real chip
        '''
        api = IBMQuantumExperience(API_TOKEN)
        parameters = api.backend_parameters()
        self.assertIsNotNone(parameters)

    def test_api_backends_availables(self):
        '''
        Check the backends availables
        '''
        api = IBMQuantumExperience(API_TOKEN)
        backends = api.available_backends()
        self.assertGreaterEqual(len(backends), 2)

    def test_api_backend_simulators_available(self):
        '''
        Check the backend simulators available
        '''
        api = IBMQuantumExperience(API_TOKEN)
        backends = api.available_backend_simulators()
        self.assertGreaterEqual(len(backends), 1)
        

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQX)
    unittest.TextTestRunner(verbosity=2).run(suite)
