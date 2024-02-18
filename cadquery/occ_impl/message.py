from enum import Enum

from OCP.Message import (
    Message_Gravity,
    Message_Messenger,
    Message_PrinterToReport,
    Message_Report,
)
from OCP.Message import Message as OCPMessage


class Level(Enum):
    trace = Message_Gravity.Message_Trace
    info = Message_Gravity.Message_Info
    warning = Message_Gravity.Message_Warning
    alarm = Message_Gravity.Message_Alarm
    fail = Message_Gravity.Message_Fail


class Message:

    messenger: Message_Messenger = OCPMessage.DefaultMessenger_s()

    @staticmethod
    def add_report() -> Message_Report:
        """
        Add a report
        """
        printer = Message_PrinterToReport()
        report = printer.Report()
        Message.messenger.AddPrinter(printer)
        return report

    @staticmethod
    def add_log(fname):
        pass

    @staticmethod
    def set_trace_level(level=Level.info):
        """
        Set trace level used for filtering OCCT messages.

        Changes the trace level of the default printer.

        :param level: trace level
        """
        for printer in Message.messenger.Printers():
            printer.SetTraceLevel(level.value)
            break


# change default OCCT logging level
Message.set_trace_level(Level.fail)
