from setuptools import setup

setup(
    name='MIapiLib',
    python_requires='>=3.10.0',
    version='1.0.0',
    description="Library to manage MI files in Scribe's platform",
    url='https://github.com/ScribeLabsAI/MIapiLib',
    author='Ailin Venerus',
    author_email='ailin@scribelabs.ai',
    packages=['MIapiLib'],
    install_requires=['requests','dotenv'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.10',
        'Topic :: Security',
        'Typing :: Typed'
    ],
)
