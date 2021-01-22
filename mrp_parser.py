from html.parser import HTMLParser
    

class XmlParser(HTMLParser):
    # outer return value
    nodes = []
    top_nodes = []
    edges = []

    # inner workings
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
            self.top_nodes.append(lm)
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

class Mrp:
    def __init__(self,xml_parser):
        self.xml_parser = xml_parser
        self.nodes = xml_parser.nodes
        self.edges = xml_parser.edges
        self.top_nodes = xml_parser.top_nodes

    def con_indent(self,n):
        return " " * n

    def con_header(self):
        retval = ""
        retval += self.con_indent(2)
        retval += "\"id\":\"1234\",\n"
        retval += self.con_indent(2)
        retval += "\"flavor\":\"1234\",\n"
        retval += self.con_indent(2)
        retval += "\"framwork\":\"1234\",\n"
        retval += self.con_indent(2)
        retval += "\"version\":\"1234\",\n"
        retval += self.con_indent(2)
        retval += "\"time\":\"1234\",\n"
        retval += self.con_indent(2)
        retval += "\"source\":\"1234\",\n"
        retval += self.con_indent(2)
        retval += "\"input\":\"1234\",\n"
        return retval

    def con_tops(self):
        retval = self.con_indent(2)
        retval += "\"tops\":[\n"
        retval += self.con_indent(4)
        retval += ",".join([str(x["nid"]) for x in self.top_nodes])
        retval += "\n"
        retval += self.con_indent(2)
        retval += "],\n"
        return retval

    def con_nodes(self):
        retval = self.con_indent(2) + "\"nodes\":[\n"
        for n in self.nodes:
            retval += self.con_indent(4)
            retval += "{\n"
            retval += self.con_indent(6)
            retval += "\"id\":" + str(n["nid"]) + ",\n"
            retval += self.con_indent(6)
            retval += "\"label\":\"" + n["label"] + "\"\n"
            retval += self.con_indent(4)
            retval += "},\n"
        retval += self.con_indent(2)
        retval += "],\n"
        return retval

    def con_edges(self):
        retval = self.con_indent(2) + "\"edges\":[\n"
        for e in self.edges:
            retval += self.con_indent(4)
            retval += "{\n"
            retval += self.con_indent(6)
            retval += "\"source\":" + str(e["source"]) + ",\n"
            retval += self.con_indent(6)
            retval += "\"target\":" + str(e["target"]) + ",\n"
            retval += self.con_indent(6)
            retval += "\"label\":\"" + e["label"] + "\"\n"
            retval += self.con_indent(4)
            retval += "}\n"
        retval += self.con_indent(2)
        retval += "]\n"
        return retval

    def toString(self):
        retval = "{\n"
        retval += self.con_header()
        retval += self.con_tops()
        retval += self.con_nodes()
        retval += self.con_edges()
        retval += "}"
        return retval

def xml2mrp(f_name):
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
    mrp = Mrp(parser)
    return mrp.toString()


f_name = "ProcessModels/Process 25.xml"

res = xml2mrp(f_name)
print(res)

