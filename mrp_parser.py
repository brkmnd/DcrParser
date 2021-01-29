from html.parser import HTMLParser
import time
import os

def get_time():
    t0 = time.localtime()
    return str(t0.tm_hour) + ":" + str(t0.tm_min) + ":" + str(t0.tm_sec)

def get_attr(attrs,attr_name):
    res = None
    for (a_name,a_val) in attrs:
        if a_name == attr_name:
            res = a_val
    return res

class XmlParser(HTMLParser):
    # outer return value
    nodes = []
    top_nodes = []
    edges = []
    desc = ""

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
                      "eid":get_attr(attrs,"eventid").strip()
                    , "nid":self.nid
                    , "label":get_attr(attrs,"labelid").strip()
                    }
            self.map_eid[lm["eid"]] = self.nid
            self.nodes.append(lm)
            self.top_nodes.append(lm)
            self.nid += 1
        elif tag == "role" and len(attrs) > 0:
            self.tag = tag
        elif tag in ["conditions","responses","excludes","includes","events","coresponses","milestones"]:
            self.tag = tag
        elif tag in ["condition","response","exclude","include","coresponse","milestone"] and self.tag in ["conditions","responses","excludes","includes","coresponses","milestones"]:
            #print(self.map_eid)
            sid = self.map_eid[get_attr(attrs,"sourceid")]
            tid = self.map_eid[get_attr(attrs,"targetid")]
            em = {
                      "source":sid
                    , "target":tid
                    , "label":tag
                    }
            self.edges.append(em)
        elif self.tag == "events":
            if tag == "event":
                self.role_eid = get_attr(attrs,"id")
            elif tag == "role":
                self.tag = "event-role"
        elif tag == "highlightlayer" and get_attr(attrs,"name") == "description":
            self.tag = "high-desc"

    def handle_endtag(self, tag):
        if tag == "role" and self.tag == tag:
            self.tag = ""
        elif tag == "role" and self.tag in ["event-role"]:
            self.tag = ""
        elif tag == "highlightlayer" and self.tag == "high-desc":
            self.tag = ""
        elif tag in ["conditions","responses","excludes","includes","events","coresponses","milestones"] and tag == self.tag:
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
        elif self.tag == "high-desc":
            self.desc = data.strip()

class Mrp:
    def __init__(self,xml_parser,fname):
        self.xml_parser = xml_parser
        self.nodes = xml_parser.nodes
        self.edges = xml_parser.edges
        self.top_nodes = xml_parser.top_nodes
        self.desc = xml_parser.desc.replace("\"","`")
        self.fname = fname
        self.id = fname.split(" ")[-1][:-4]

        if self.desc == "":
            print("warning, empty description for" + fname)

    def con_indent(self,n):
        return " " * n

    def con_header(self):
        retval = ""
        retval += self.con_indent(2)
        retval += "\"id\":\"" + self.id + "\",\n"
        retval += self.con_indent(2)
        retval += "\"flavor\":2,\n"
        retval += self.con_indent(2)
        retval += "\"framework\":\"dcr\",\n"
        retval += self.con_indent(2)
        retval += "\"version\":1.0,\n"
        retval += self.con_indent(2)
        retval += "\"time\":\"" + get_time() + "\",\n" # time for convertion
        retval += self.con_indent(2)
        retval += "\"source\":\""+self.fname+"\",\n"
        retval += self.con_indent(2)
        retval += "\"input\":\"" + self.desc + "\",\n"
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
            retval += "},\n"
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

def xml2mrp(fname):
    with open("ProcessModels/" + fname,"r") as f:
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
    mrp = Mrp(parser,fname)
    return mrp.toString()


def save_mrp(txt,fname):
    fname = "Mrps/" + fname + ".mrp"
    with open(fname,"w") as f:
        f.write(txt)
    print("saved '" + fname + "'")

if __name__ == "__main__":
    fs = os.listdir("ProcessModels")
    for fname in fs:
        if fname[-4:] == ".swp":
            continue
        res = xml2mrp(fname)
        save_mrp(res,fname[:-4])

