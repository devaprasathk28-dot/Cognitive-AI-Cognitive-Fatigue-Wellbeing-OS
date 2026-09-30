# ======================================================
# WINDOWS SERVICE FOR COGNITIVE FATIGUE ENGINE
# ======================================================

import win32serviceutil
import win32service
import win32event
import servicemanager
import time
import sys
import os
import logging
from datetime import datetime

# -----------------------------
# FIX WORKING DIRECTORY
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)
sys.path.append(BASE_DIR)

from monitor.fatigue_score_engine import CognitiveFatigueModel

# -----------------------------
# LOGGING SETUP
# -----------------------------
LOG_FILE = os.path.join(BASE_DIR, "data", "service_error.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ======================================================
# SERVICE CLASS
# ======================================================

class CognitiveService(win32serviceutil.ServiceFramework):

    _svc_name_ = "CognitiveFatigueService"
    _svc_display_name_ = "Cognitive Fatigue AI Engine"
    _svc_description_ = "Background cognitive fatigue monitoring system"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)

        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

        self.running = True
        self.model = None

    # -------------------------------------------------
    # STOP SERVICE
    # -------------------------------------------------

    def SvcStop(self):

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        self.running = False
        win32event.SetEvent(self.stop_event)

        logging.info("Service stopping")

    # -------------------------------------------------
    # START SERVICE
    # -------------------------------------------------

    def SvcDoRun(self):

        servicemanager.LogInfoMsg("Cognitive Fatigue Service Started")
        logging.info("Service started")

        # Report running state to Windows
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        try:
            self.main()
        except Exception as e:
            logging.exception("Service crashed")

    # -------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------

    def main(self):

        self.model = CognitiveFatigueModel()

        logging.info("Cognitive model initialized")

        while self.running:

            try:

                category = "Development"
                duration = 60
                hour = datetime.now().hour

                state = self.model.update(category, duration, hour)

                logging.info(
                    f"Fatigue={state['fatigue_score']} Level={state['level']}"
                )

                # Wait or stop
                rc = win32event.WaitForSingleObject(self.stop_event, 60000)

                if rc == win32event.WAIT_OBJECT_0:
                    break

            except Exception:
                logging.exception("Runtime error in service loop")
                time.sleep(10)


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(CognitiveService)
