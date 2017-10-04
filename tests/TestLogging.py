import unittest
import mock
from copy import copy
from tests import BaseTest

import logging

# Units under test
import cadquery
from cadquery.freecad_impl import console_logging


class TestLogging(BaseTest):
    def setUp(self):
        # save root logger's state
        root_logger = logging.getLogger()
        self._initial_level = root_logger.level
        self._initial_logging_handlers = copy(root_logger.handlers)

    def tearDown(self):
        # forcefully re-establish original log state
        root_logger = logging.getLogger()
        root_logger.level = self._initial_level
        root_logger.handlers = self._initial_logging_handlers
        # reset console_logging's global state
        cadquery.freecad_impl.console_logging._logging_handler = None

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleMessage(self, mock_freecad):
        console_logging.enable()
        log = logging.getLogger('test')

        log.info('foo')
        mock_freecad.Console.PrintMessage.assert_called_once_with('foo\n')
        mock_freecad.Console.PrintWarning.assert_not_called()
        mock_freecad.Console.PrintError.assert_not_called()

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleWarning(self, mock_freecad):
        console_logging.enable()
        log = logging.getLogger('test')

        log.warning('bar')
        mock_freecad.Console.PrintMessage.assert_not_called()
        mock_freecad.Console.PrintWarning.assert_called_once_with('bar\n')
        mock_freecad.Console.PrintError.assert_not_called()

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleError(self, mock_freecad):
        console_logging.enable()
        log = logging.getLogger('test')

        log.error('roo')
        mock_freecad.Console.PrintMessage.assert_not_called()
        mock_freecad.Console.PrintWarning.assert_not_called()
        mock_freecad.Console.PrintError.assert_called_once_with('roo\n')

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleDebugOffDefault(self, mock_freecad):
        console_logging.enable()
        log = logging.getLogger('test')

        log.debug('no show')
        mock_freecad.Console.PrintMessage.assert_not_called()
        mock_freecad.Console.PrintWarning.assert_not_called()
        mock_freecad.Console.PrintError.assert_not_called()

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleSetLevelDebug(self, mock_freecad):
        console_logging.enable(level=logging.DEBUG)
        log = logging.getLogger('test')

        log.debug('now showing')
        mock_freecad.Console.PrintMessage.assert_called_once_with('now showing\n')

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleSetLevelWarning(self, mock_freecad):
        console_logging.enable(level=logging.WARNING)
        log = logging.getLogger('test')

        log.info('no show')
        log.warning('be warned')
        mock_freecad.Console.PrintMessage.assert_not_called()
        mock_freecad.Console.PrintWarning.assert_called_once_with('be warned\n')

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleLogFormat(self, mock_freecad):
        console_logging.enable(format=">> %(message)s <<")
        log = logging.getLogger('test')

        log.info('behold brackets!')
        mock_freecad.Console.PrintMessage.assert_called_once_with('>> behold brackets! <<\n')

    @mock.patch('cadquery.freecad_impl.console_logging.FreeCAD')
    def testConsoleEnableDisable(self, mock_freecad):
        console_logging.enable()
        console_logging.disable()
        log = logging.getLogger('test')

        log.error('nope, disabled')
        mock_freecad.Console.PrintError.assert_not_called()
