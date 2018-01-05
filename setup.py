from setuptools import setup

with open('requirements.txt') as f:
    install_requires = f.readlines()

setup(
    name='cloudwatch-json-logs',
    version='0.0.1',
    description='CloudWatch JSON logs client',
    author='Rob Young',
    author_email='rob@robyoung.digital',
    py_modules=[
        'cjl'
    ],
    install_requires=install_requires,

    entry_points={
        'console_scripts': [
            'cjl = cjl:main'
        ]
    }
)
