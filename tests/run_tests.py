import unittest
import os


def main():
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)

    # Set the tests directory path
    tests_directory = os.path.join(current_directory, 'halina')

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_directory, pattern='test_*.py')

    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    main()
