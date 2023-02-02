from collections import deque


class Masid:
    msgid_dqu = deque(maxlen=1000)

    def __init__(self, msgid):
        self.msgid = msgid

    def Query_id(self):
        if self.msgid in Masid.msgid_dqu:
            return 1
        else:
            Masid.msgid_dqu.append(self.msgid)
            return 0

