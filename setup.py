from setuptools import setup, find_packages

setup(
    name='arquivos_em_rede_local',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # Adicione aqui as dependências do seu projeto
    ],
    entry_points={
        'console_scripts': [
            'arquivos_em_rede_local=main:main',
        ],
    },
    author='Tony Albert Lima, Jean Sidney Oliveira dos Santos'
)