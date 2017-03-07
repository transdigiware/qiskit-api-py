from setuptools import setup

setup(name = 'IBMQuantumExperience',
      packages = ['IBMQuantumExperience'], # this must be the same as the name above
      version='1.1.0',
      author='IBM Research ETX',
      description='A Python library for the Quantum Experience API.',
      author_email='fmartinfdez@gmail.com',
      url = 'https://github.com/IBM/qiskit-api-py',
      keywords = ['ibm', 'quantum computer', 'quantum experience'],
      license='Apache-2.0',
      install_requires=[
        'requests'
      ],
      zip_safe=False)
