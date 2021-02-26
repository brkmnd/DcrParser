from html.parser import HTMLParser
import time
import os
import re

def get_time():
    t0 = time.localtime()
    return str(t0.tm_hour) + ":" + str(t0.tm_min) + ":" + str(t0.tm_sec)

def get_attr(attrs,attr_name):
    res = None
    for (a_name,a_val) in attrs:
        if a_name == attr_name:
            res = a_val
    assert (res != None),"could not find attribute '" + attr_name + "' in " + str(attrs)
    return res

class XmlParser(HTMLParser):

    edgelabels = ["condition","response","exclude","include","coresponse","milestone"] 
    edgelabels_parents_0events = ["conditions","responses","excludes","includes","coresponses","milestones"]
    edgelabels_parents = edgelabels_parents_0events + ["events"]
    
    def __init__(self,fname):
        super().__init__()

        self.fname = fname

        # outer return value
        self.nodes = []
        self.top_nodes = []
        self.edges = []
        self.desc = ""

        # inner workings
        # id of events/activities
        self.map_eid = {}
        # id of roles
        self.map_rid = {}
        # from event to role
        self.map_event2role = []
        self.nid = 0
        self.tag = ""

        # for event roles
        self.role_eventid = ""

    def handle_starttag(self, tag, attrs):
        if tag == "labelmapping":
            lm = {    "eid":get_attr(attrs,"eventid").strip()
                    , "nid":self.nid
                    , "label":get_attr(attrs,"labelid").strip()
                    }
            self.map_eid[lm["eid"]] = self.nid
            self.nodes.append(lm)
            self.top_nodes.append(lm)
            self.nid += 1
        elif tag == "role" and len(attrs) > 0 and not self.tag in ["event2role","events"]:
            self.tag = tag
        elif tag in self.edgelabels_parents:
            self.tag = tag
        elif tag in self.edgelabels and self.tag in self.edgelabels_parents_0events:
            sid = self.map_eid[get_attr(attrs,"sourceid")]
            tid = self.map_eid[get_attr(attrs,"targetid")]
            em = {    "source":sid
                    , "target":tid
                    , "label":tag
                    , "source_name":get_attr(attrs,"sourceid")
                    , "target_name":get_attr(attrs,"targetid")
                    }
            self.edges.append(em)
        elif self.tag == "events" and tag == "event":
            self.role_eventid = get_attr(attrs,"id").strip()
        elif self.tag == "events" and tag == "role":
            self.tag = "event2role"
        elif tag == "highlightlayer" and get_attr(attrs,"name") == "description":
            self.tag = "high-desc"

    def handle_endtag(self, tag):
        if tag == "role" and self.tag == "event2role":
            self.tag = "events"
        if tag == "role" and self.tag == "role":
            self.tag = ""
        elif tag == "highlightlayer" and self.tag == "high-desc":
            self.tag = ""
        elif tag in self.edgelabels_parents and tag == self.tag:
            self.tag = ""

    def handle_data(self, data):
        if self.tag == "role":
            lm = {    "nid":self.nid
                    , "label":data
                    }
            self.nodes.append(lm)
            self.map_rid[lm["label"]] = self.nid
            self.nid += 1
        elif self.tag == "event2role":
            data = data.strip()
            if self.role_eventid == "" or data == "":
                print("warning in " + self.fname + ": empty event2role: '" + self.role_eventid + "' -> '" + data + "'")
            #print("[" + self.fname + "]" + self.role_eventid + "->" + data)
            self.map_event2role.append((self.role_eventid,data))
        elif self.tag == "high-desc":
            self.desc = data.strip()

class Mrp:
    def __init__(self,xml_parser,fname,id0):
        self.xml_parser = xml_parser
        self.nodes = xml_parser.nodes
        self.edges = xml_parser.edges
        self.top_nodes = xml_parser.top_nodes
        self.desc = xml_parser.desc.strip().replace("\"","'").replace("\n"," ")
        self.desc = re.sub("\s+"," ",self.desc)
        self.desc = self.desc.encode("ascii","ignore").decode("utf-8") # remove strange chars
        self.fname = fname
        self.id = str(id0)
        self.time = get_time()

        if self.desc == "":
            print("warning, empty description for" + fname)

    def con_indent(self,n):
        return " " * n

    def con_header(self,framework):
        retval  = "\"id\":\"" + self.id + "\","
        retval += "\"flavor\":2,"
        retval += "\"framework\":\"" + framework + "\","
        retval += "\"version\":1.1,"
        #retval += "\"time\":\"" + self.time + "\"," # time for convertion
        retval += "\"time\": \"2021-02-09\", "
        retval += "\"source\":\""+self.fname+"\","
        retval += "\"input\":\"" + self.desc + "\","

        return retval

    def con_tops(self):
        retval  = "\"tops\":["
        retval += ",".join([str(x["nid"]) for x in self.top_nodes])
        retval += "],"
        return retval

    def con_nodes(self):
        def create_node(nid,l):
            retval  = "{"
            retval += "\"id\":" + str(nid) + ","
            retval += "\"label\":\"" + l + "\""
            retval += "}"
            return retval

        ns = [create_node(x["nid"],x["label"]) for x in self.nodes]
        retval  = "\"nodes\":["
        retval += ",".join(ns)
        retval += "],"
        return retval

    def con_edges(self):
        def create_edge(x):
            retval  = "{"
            retval += "\"source\":" + str(x["source"]) + ","
            retval += "\"target\":" + str(x["target"]) + ","
            retval += "\"label\":\"" + x["label"] + "\""
            retval += "}"
            #print(x["source_name"] + " -[" + x["label"] + "]> " + x["target_name"])
            return retval

        edges = [create_edge(x) for x in self.edges]
        retval  = "\"edges\":["
        retval += ",".join(edges)
        retval += "]"
        return retval

    def create_input(self):
        retval  = "{"
        retval += "\"id\": \"" + self.id + "\", "
        retval += "\"version\": 1.1, "
        #retval += "\"time\": \"" + self.time + "\", "
        retval += "\"time\": \"2021-02-09\", "
        retval += "\"language\": \"eng\", "
        retval += "\"source\": \"lpps\", "
        retval += "\"provenance\": \"MRP 2020\", "
        retval += "\"targets\": [\"eds\", \"amr\", \"ucca\", \"ptg\"], "
        retval += "\"input\": " + "\"" + self.desc + "\"" 
        retval += "}"
        return retval

    def toString(self,framework):
        retval = "{"
        retval += self.con_header(framework)
        retval += self.con_tops()
        retval += self.con_nodes()
        retval += self.con_edges()
        retval += "}"
        return retval

def xml2mrp(fname,id0):
    with open("ProcessModels/" + fname,"r") as f:
        parser = XmlParser(fname)
        parser.feed(f.read())
    role_edges = []
    for (evnt,role) in parser.map_event2role:
        em = {      "source":parser.map_eid[evnt]
                  , "target":parser.map_rid[role]
                  , "label":"role"
                  , "source_name":evnt
                  , "target_name":role
                  }
        role_edges.append(em)
    parser.edges = role_edges + parser.edges
    mrp = Mrp(parser,fname,id0)
    return mrp


def save_data(txt,fname):
    #fname = "models/2020/cf/" + fname + ".mrp"
    fname = "mrp_data/2020/cf/" + fname
    with open(fname,"w") as f:
        f.write(txt)
    print("saved '" + fname + "'")

def main():
    fs = os.listdir("ProcessModels")
    res = []
    descs = []
    id0 = 1

    for fname in fs:
        if fname[-4:] == ".swp":
            continue
        #print(str(id0) + ":" + fname)
        mrp = xml2mrp(fname,id0)
        res.append(mrp)
        descs.append(mrp.desc)
        id0 += 1

    res_train_amr = [x.toString("amr") for x in res[:-10]]
    res_train_ucca = [x.toString("ucca") for x in res[:-10]]
    res_val_amr = [x.toString("amr") for x in res[-10:-5]]
    res_val_ucca = [x.toString("ucca") for x in res[-10:-5]]
    res_eval = [x.create_input() for x in res[-5:]]
    
    save_data("\n".join(res_train_ucca),"training/ucca.mrp")
    save_data("\n".join(res_train_amr),"training/amr.mrp")
    save_data("\n".join(res_val_ucca),"validation/ucca.mrp")
    save_data("\n".join(res_val_amr),"validation/amr.mrp")
    save_data("\n".join(res_eval),"evaluation/input.mrp")
    save_data("\n".join(descs),"companion/udpipe.txt")

if __name__ == "__main__":
    main()

