import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HALINA_DIR = os.path.join(ROOT_DIR, 'src', 'halina')
RESOURCES_DIR = os.path.join(HALINA_DIR, 'email_rapport', 'resources')
TEST_DIR = os.path.join(ROOT_DIR, 'tests')
TEST_RESOURCES_DIR = os.path.join(TEST_DIR, 'resources')
CONFIG_DIR = os.path.join(ROOT_DIR, 'configuration')
SIMULATOR_DIR = os.path.join(ROOT_DIR, 'src', 'simulator')
