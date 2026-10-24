"""Shared failure reporting for browser checks."""
import os
import unittest


class AnnotatedBrowserResult(unittest.TextTestResult):
    """Keep CI failures readable when signed job-log downloads are unavailable."""
    def annotate(self, test, error):
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            message = self._exc_info_to_string(error, test)[-12000:]
            message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f'::error title=Browser regression failure::{message}', flush=True)

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.annotate(test, error)

    def addError(self, test, error):
        super().addError(test, error)
        self.annotate(test, error)


    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error is not None:
            self.annotate(subtest, error)


