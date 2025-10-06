from datetime import datetime, timezone

class DateTime():
    def __init__(self):
        self.utc_now = datetime.now(timezone.utc)
        self.ist_now = datetime.now()


    def ist(self):
        return self.ist_now.strftime("%Y-%m-%d %H:%M:%S")

    def utc(self):
        return self.utc_now.strftime("%Y-%m-%d %H:%M:%S")
    


obj = DateTime()
ist = obj.ist()
utc = obj.utc()