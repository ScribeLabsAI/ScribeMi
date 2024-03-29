from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='scribemi',
    python_requires='>=3.10.0',
    version='1.3.0',
    description="Library to manage MI files in Scribe's platform",
    long_description=readme(),
    url='https://github.com/ScribeLabsAI/ScribeMi',
    long_description_content_type='text/markdown',
    author='Ailin Venerus',
    author_email='ailin@scribelabs.ai',
    packages=['scribemi'],
    install_requires=['requests', 'scribeauth', 'aws_requests_auth'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.10',
        'Typing :: Typed'
    ],
)
