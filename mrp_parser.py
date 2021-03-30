from html.parser import HTMLParser
import time
import os
import re
import html
import unidecode

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
        self.anchors = {}

        # inner workings
        # id of events/activities
        self.map_eid = {}
        # id of roles
        self.map_rid = {}
        # from event to role
        self.map_event2role = []
        self.nid = 0
        self.tag = ""
        self.anch_pos = None

        # for event roles
        self.role_eventid = ""

    def handle_starttag(self, tag, attrs):
        if tag == "labelmapping":
            lm = {    "eid":get_attr(attrs,"eventid").strip()
                    , "nid":self.nid
                    , "label":get_attr(attrs,"labelid")
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
        elif tag == "highlights":
            self.tag = "highlight-pos"
        elif tag == "range" and self.tag == "highlight-pos":
            tag_start = int(get_attr(attrs,"start").strip())
            tag_end = int(get_attr(attrs,"end").strip())
            self.anch_pos = tag_start,tag_end
        elif tag == "item" and self.tag == "highlight-pos":
            anch_label = get_attr(attrs,"id").strip()
            if anch_label not in self.anchors:
                self.anchors[anch_label] = []
            if not self.anch_pos in self.anchors[anch_label] and self.anch_pos[0] < self.anch_pos[1]:
                self.anchors[anch_label].append(self.anch_pos)
            self.anch_pos = None

    def handle_endtag(self, tag):
        if tag == "role" and self.tag == "event2role":
            self.tag = "events"
        if tag == "role" and self.tag == "role":
            self.tag = ""
        elif tag == "highlightlayer" and self.tag == "high-desc":
            self.tag = ""
        elif tag == "highlights":
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
            self.desc = data


def list_tokens_desc(desc):
    rx = "[a-zA-Z0-9][a-zA-Z0-9'\\-]+|[.,\\-_]"
    mre = re.compile(rx)
    res = []
    for m in mre.finditer(desc):
        res.append((m.group(),m.start(),m.end()))
    return res

def create_desc2(desc,fname):
    desc = html.unescape(desc)
    desc = desc.replace("\u200b","") #blank/zero-space chars
    desc = desc.replace("\u00A0"," ") #non-breaking wspace
    desc = desc.replace("\n"," ") #keep newlines
    #desc = re.sub(" +"," ",desc) #collapse spaces
    desc = unidecode.unidecode(desc)
    desc = desc.replace("\"","'")
    return desc

def create_desc3(desc):
    desc = desc.encode('ascii', 'ignore').decode("utf-8")
    desc = desc.replace("\"","'")
    desc = desc.replace("\n",";")
    return desc

class Mrp:
    def __init__(self,xml_parser,fname,id0):
        self.xml_parser = xml_parser
        self.nodes = xml_parser.nodes
        self.edges = xml_parser.edges
        self.anchors = xml_parser.anchors
        self.top_nodes = xml_parser.top_nodes

        self.fname = fname
        self.id = str(id0)
        self.time = get_time()
        self.flavor = 2
        self.include_anchs = False

        max_tokens_desc = 350
        desc = xml_parser.desc
        self.desc = create_desc2(desc,fname)
        self.cutoff_desc(self.desc,max_tokens_desc)

        if self.desc == "":
            print("warning, empty description for" + fname)

    def cutoff_desc(self,desc,max_ts):
        c0 = len(desc)
        if max_ts > 0:
            desc_ts = list_tokens_desc(desc)
            if len(desc_ts) > max_ts:
                print("--cutoff " + str(len(desc_ts) - max_ts) + " tokens from '" + self.fname + "'")
                last_t = desc_ts[max_ts]
                c0 = last_t[2]
        self.cutoff_anchs(c0)
        self.desc = desc[:c0]

    def cutoff_anchs(self,i):
        res = {}
        nr_cutoffs = 0
        for a in self.anchors.keys():
            ares = []
            for atup in self.anchors[a]:
                if atup[0] > i or atup[1] > i:
                    nr_cutoffs += 1
                    continue
                ares.append(atup)
            res[a] = ares
        if nr_cutoffs > 0:
            print("--cutoff " + str(nr_cutoffs) + " anchors from '" + self.fname + "'")
            self.anchors = res

    def test_anchors(self):
        for x in self.nodes:
            l = x["label"]
            eid = l
            if "eid" in x:
                eid = x["eid"]
            if eid in self.anchors:
                for a in self.anchors[eid]:
                    s0 = self.desc[a[0]:a[1]]
                    print("")
                    print("-label: '" + l + "'")
                    print("-res  : '" + s0 + "'")
                    print("*pos-org: " + str(a))

    def con_indent(self,n):
        return " " * n

    def con_header(self,framework):
        retval  = "\"id\":\"" + self.id + "\","
        retval += "\"flavor\":" + str(self.flavor) + " ,"
        retval += "\"language\":\"eng\" ,"
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
        nr_anchors = 0

        def create_anchors(x):
            nonlocal nr_anchors

            if not self.include_anchs:
                return ""
            if "eid" in x:
                eid = x["eid"]
            else:
                eid = x["label"]

            anchors = None
            if eid in self.anchors:
                anchors = ["{\"from\":" + str(a[0]) + ",\"to\":" + str(a[1]) + "}" for a in self.anchors[eid]]

            if anchors is None or len(anchors) <= 0:
                return ""

            nr_anchors += 1
            retval  = ",\"anchors\":["
            retval += ",".join(anchors)
            retval += "]"
            return retval

        def create_node(x):
            nid = x["nid"]
            l = x["label"]
            retval  = "{"
            retval += "\"id\":" + str(nid) + ","
            retval += "\"label\":\"" + l + "\""
            retval += create_anchors(x)
            retval += "}"
            #print(retval)
            return retval
    
        ns = [create_node(x) for x in self.nodes]

        if nr_anchors <= 0 and self.include_anchs:
            print("--no anchors for '" + self.fname + "'")

        #self.test_anchors()

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
        retval += "\"targets\": [\"eds\", \"amr\", \"ucca\", \"ptg\", \"dcr\"], "
        retval += "\"input\": " + "\"" + self.desc + "\"" 
        retval += "}"
        return retval

    def toString(self,framework,flavor=2,include_anchs=True):
        self.flavor = flavor
        self.include_anchs = include_anchs
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

def sort_files(fs,stype_fun):
    no_anchs = ['P05.xml', 'P06.xml', 'P10.xml', 'P15.xml', 'P16.xml', 'P18.xml', 'P19.xml', 'P20.xml', 'P22.xml', 'P23.xml', 'P25.xml']
    stypes = {"normal":1,"by-anchs":2,"none":3}
    stype = stype_fun(stypes)
    is_not_xml = lambda x: x[-4:] == ".swp" or ".xml" not in x
    if stype == stypes["normal"]:
        fss = fs
        fss.sort()
        res = []
        for fname in fss:
            if is_not_xml(fname):
                continue
            res.append(fname)
        return res
    elif stype == stypes["by-anchs"]:
        fss = fs
        fss.sort()
        res_h = []
        res_t = []
        for fname in fss:
            if is_not_xml(fname):
                continue
            if fname in no_anchs:
                res_t.append(fname)
            else:
                res_h.append(fname)
        return res_h + res_t
    else:
        return fs

def main():
    fs = os.listdir("ProcessModels")
    fs = sort_files(fs,lambda t: t["normal"])
    res = []
    descs = []
    id0 = 1
    flavor = 1

    is_testing = False
    if is_testing:
        m0 = xml2mrp("P01.xml",1)
        m0.toString("dcr",flavor,True)
        return True

    for fname in fs:
        #print(str(id0) + ":" + fname)
        mrp = xml2mrp(fname,id0)
        res.append(mrp)
        descs.append(mrp.desc)
        id0 += 1

    res_train_ucca = [x.toString("ucca",flavor) for x in res[:-10]]
    res_val_ucca = [x.toString("ucca",flavor) for x in res[-10:-5]]

    res_train_amr = [x.toString("amr",flavor,False) for x in res[:-10]]
    res_val_amr = [x.toString("amr",flavor,False) for x in res[-10:-5]]

    res_train_dcr = [x.toString("dcr",flavor,True) for x in res[:-10]]
    res_val_dcr = [x.toString("dcr",flavor,True) for x in res[-10:-5]]

    res_eval = [x.create_input() for x in res[-5:]]

    return True
    
    save_data("\n".join(res_train_ucca),"training/ucca.mrp")
    save_data("\n".join(res_val_ucca),"validation/ucca.mrp")

    save_data("\n".join(res_train_amr),"training/amr.mrp")
    save_data("\n".join(res_val_amr),"validation/amr.mrp")

    save_data("\n".join(res_train_dcr),"training/dcr.mrp")
    save_data("\n".join(res_val_dcr),"validation/dcr.mrp")

    save_data("\n".join(res_eval),"evaluation/input.mrp")
    save_data("\n".join(descs),"companion/udpipe.txt")

if __name__ == "__main__":
    main()

