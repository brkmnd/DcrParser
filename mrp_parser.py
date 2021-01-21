from html.parser import HTMLParser
    

class XmlParser(HTMLParser):
    nodes = []
    edges = []
    # id of events
    map_eid = {}
    # id of roles
    map_rid = {}
    # from event to role
    map_events = []
    nid = 0
    tag = ""
    
    # for event roles
    role_eid = ""
    def handle_starttag(self, tag, attrs):
        if tag == "labelmapping":
            lm = {
                      "eid":attrs[0][1]
                    , "nid":self.nid
                    , "label":attrs[1][1]
                    }
            self.map_eid[lm["eid"]] = self.nid
            self.nodes.append(lm)
            self.nid += 1
        elif tag == "role" and len(attrs) > 0:
            self.tag = tag
        elif tag in ["conditions","responses","excludes","includes","events"]:
            self.tag = tag
        elif tag in ["condition","response","exclude","include"] and self.tag in ["conditions","responses","excludes","includes"]:
            sid = self.map_eid[attrs[0][1]]
            tid = self.map_eid[attrs[1][1]]
            em = {
                      "source":sid
                    , "target":tid
                    , "label":tag
                    }
            self.edges.append(em)
        elif self.tag == "events":
            if tag == "event":
                self.role_eid = attrs[0][1]
            elif tag == "role":
                self.tag = "event-role"

    def handle_endtag(self, tag):
        if tag == "role" and self.tag == tag:
            self.tag = ""
        elif tag in ["conditions","responses","excludes","includes","events"] and tag == self.tag:
            self.tag = ""

    def handle_data(self, data):
        if self.tag == "role":
            lm = {
                      "nid":self.nid
                    , "label":data
                    }
            self.nodes.append(lm)
            self.map_rid[lm["label"]] = self.nid
            self.nid += 1
        elif self.tag == "event-role" and self.role_eid != "":
            self.map_events.append((self.role_eid,data))
            self.tag = "events"
            self.role_eid = ""


f_name = "ProcessModels/Process 25.xml"

def get_xml():
    with open(f_name,"r") as f:
        parser = XmlParser()
        parser.feed(f.read())
    role_edges = []
    for (evnt,role) in parser.map_events:
        em = {
                    "source":parser.map_eid[evnt]
                  , "target":parser.map_rid[role]
                  , "label":"role"
                }
        role_edges.append(em)
    parser.edges = role_edges + parser.edges
    return parser

p = get_xml()
print(p.edges)

