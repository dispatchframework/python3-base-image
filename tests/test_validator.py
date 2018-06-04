import os
import unittest
import unittest.mock

from validator import validator


class TestValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handlers_path = os.path.dirname(os.path.realpath(__file__)) + '/handlers'

    def test_good_handler(self):
        args = ['validator.py', self.handlers_path, 'good_handler.handle']

        with unittest.mock.patch('sys.argv', args):
            validator.main()

    def test_missing_args_handler(self):
        args = ['validator.py', self.handlers_path, 'missing_args_handler.handle']

        with unittest.mock.patch('sys.argv', args):
            self.assertRaises(TypeError, validator.main)

    def test_non_function_handler(self):
        args = ['validator.py', self.handlers_path, 'non_function_handler.handle']

        with unittest.mock.patch('sys.argv', args):
            self.assertRaises(TypeError, validator.main)

    def test_missing_handler_name(self):
        args = ['validator.py', self.handlers_path, 'good_handler']

        with unittest.mock.patch('sys.argv', args):
            self.assertRaises(ValueError, validator.main)

    def test_non_existent_handler(self):
        args = ['validator.py', self.handlers_path, 'good_handler.non_existent_handler']

        with unittest.mock.patch('sys.argv', args):
            self.assertRaises(AttributeError, validator.main)

    def test_non_existent_file(self):
        args = ['validator.py', self.handlers_path, 'non_existent_file.handle']
        with unittest.mock.patch('sys.argv', args):
            self.assertRaises(ModuleNotFoundError, validator.main)


if __name__ == '__main__':
    unittest.main()
