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

def has_node_with_label(nodes,label):
    for n in nodes:
        if n["label"] == label:
            return True
    return False

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
            label = get_attr(attrs,"labelid")
            lm = {    "eid":get_attr(attrs,"eventid").strip()
                    , "nid":self.nid
                    , "label":label
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
            # some roles might be defined twice
            if not has_node_with_label(self.nodes,data):
                self.nodes.append(lm)
                self.map_rid[lm["label"]] = self.nid
                self.nid += 1
        elif self.tag == "event2role":
            data = data.strip()
            if self.role_eventid == "" or data == "":
                print("warning in " + self.fname + ": empty event2role: '" + self.role_eventid + "' -> '" + data + "'")
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
    def __init__(self,xml_parser,fname,id0,do_cutoff=True):
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
        self.testing_mode = False
        self.do_cutoff = do_cutoff

        max_tokens_desc = 350
        desc = xml_parser.desc
        self.desc = create_desc2(desc,fname)
        self.full_desc = self.desc
        if do_cutoff:
            self.cutoff_desc(self.desc,max_tokens_desc)

        if self.desc == "":
            print("warning, empty description for " + fname)


        self.stats = { "full desc count":len(list_tokens_desc(self.full_desc))
                     , "desc count":len(list_tokens_desc(self.desc))
                     , "nr nodes":len(self.nodes)
                     , "nr edges":len(self.edges)
                     }

    def cutoff_desc(self,desc,max_ts):
        if max_ts > 0:
            desc_ts = list_tokens_desc(desc)
            if len(desc_ts) > max_ts:
                print("--cutoff " + str(len(desc_ts) - max_ts) + " tokens from '" + self.fname + "'")
                last_t = desc_ts[max_ts]
                c0 = last_t[2]

                #cut off what else needs
                anch_cutoffs = self.cutoff_anchs(c0)
                node_cutoffs = self.cutoff_nodes(anch_cutoffs)
                self.cutoff_edges(node_cutoffs)

                self.desc = desc[:c0]

                return True
        
        return False

    def cutoff_anchs(self,i):
        res = {}
        cutoffs = {}
        nr_cutoffs = 0
        for a in self.anchors.keys():
            if a not in res:
                res[a] = []
            if a not in cutoffs:
                cutoffs[a] = []
            for atup in self.anchors[a]:
                if atup[0] > i or atup[1] > i:
                    nr_cutoffs += 1
                    cutoffs[a].append(atup)
                else:
                    res[a].append(atup)

        #refine results
        del_from_res = []
        del_from_cutoffs = []
        for a in res.keys():
            if len(res[a]) == 0:
                del_from_res.append(a)
        for a in cutoffs.keys():
            if len(cutoffs[a]) == 0:
                del_from_cutoffs.append(a)
        for a in del_from_res:
            del res[a]
        for a in del_from_cutoffs:
            del cutoffs[a]
        for a in cutoffs.keys():
            # Íf some nodes are present where some anchors are cut off, some are not
            # then remove this node from res. We do not want it at all
            if a in res:
                del res[a]

        if len(cutoffs) == 0:
            return None
        else:
            print("--cutoff " + str(nr_cutoffs) + " anchors from '" + self.fname + "'")
            self.anchs = res
            return cutoffs

    def cutoff_nodes(self,anch_cutoffs):
        if anch_cutoffs is None:
            return None

        res = []
        res_tops = []
        cutoffs = []

        for node in self.nodes:
            did_cutoff = False
            for a in anch_cutoffs.keys():
                if ("eid" in node and node["eid"] == a) or ("eid" not in node and node["label"] == a):
                    cutoffs.append(node)
                    did_cutoff = True
                    break
            if not did_cutoff:
                res.append(node)
                if "eid" in node:
                    res_tops.append(node)

        if len(cutoffs) == 0:
            return None
        else:
            self.nodes = res
            self.top_nodes = res_tops
            print("--cutoff " + str(len(cutoffs)) + " nodes from '" + self.fname + "'")
            return cutoffs

    def cutoff_edges(self,node_cutoffs):
        if node_cutoffs is None:
            return None

        res = []
        cutoffs = []
        for e in self.edges:
            did_cutoff = False
            for n in node_cutoffs:
                if n["nid"] == e["source"] or n["nid"] == e["target"]:
                    cutoffs.append(e)
                    did_cutoff = True
                    break
            if not did_cutoff:
                res.append(e)

        if len(cutoffs) > 0:
            self.edges = res
            print("--cutoff " + str(len(cutoffs)) + " edges from '" + self.fname + "'")
            return cutoffs
        else:
            return None

    def test_anchors(self):
        retval = ""
        for x in self.nodes:
            l = x["label"]
            eid = l
            if "eid" in x:
                eid = x["eid"]
            if eid in self.anchors:
                for a in self.anchors[eid]:
                    s0 = self.desc[a[0]:a[1]]
                    retval += "\n"
                    retval += "-label: '" + l + "'\n"
                    retval += "-res  : '" + s0 + "'\n"
                    retval += "*pos-org: " + str(a) + "\n"
        return retval

    def con_indent(self,n):
        if self.testing_mode:
            return " " * n
        else:
            return ""
    def con_newline(self,n=1):
        if self.testing_mode:
            return "\n" * n
        else:
            return ""

    def con_header(self,framework):
        nl = self.con_newline()
        ind = self.con_indent(2)
        retval  = ind + "\"id\":\"" + self.id + "\"," + nl
        retval += ind + "\"flavor\":" + str(self.flavor) + " ," + nl
        retval += ind + "\"language\":\"eng\" ," + nl
        retval += ind + "\"framework\":\"" + framework + "\"," + nl
        retval += ind + "\"version\":1.1," + nl
        #retval += "\"time\":\"" + self.time + "\"," # time for convertion
        retval += ind + "\"time\": \"2021-02-09\", " + nl
        retval += ind + "\"source\":\""+self.fname+"\"," + nl
        retval += ind + "\"input\":\"" + self.desc + "\"," + nl

        return retval

    def con_tops(self):
        retval  = self.con_indent(2) 
        retval += "\"tops\":["
        retval += ",".join([str(x["nid"]) for x in self.top_nodes])
        retval += "],"
        retval += self.con_newline()
        return retval

    def con_nodes(self):
        nr_anchors = 0
        nl = self.con_newline()
        ind1 = self.con_indent(2)
        ind2 = self.con_indent(4)
        ind3 = self.con_indent(6)

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
                anchors = []
                return ""
            else:
                nr_anchors += 1

            retval  = ind3 + ",\"anchors\":["
            retval += ",".join(anchors)
            retval += "]" + nl
            return retval

        def create_node(x):
            nid = x["nid"]
            l = x["label"]
            retval  = "{" + nl
            retval += ind3 + "\"id\":" + str(nid) + "," + nl
            retval += ind3 + "\"label\":\"" + l + "\"" + nl
            retval += create_anchors(x)
            retval += ind2 + "}" + nl
            #print(retval)
            return retval
    
        ns = [create_node(x) for x in self.nodes]

        if nr_anchors <= 0 and self.include_anchs:
            print("--no anchors for '" + self.fname + "'")

        #self.test_anchors()

        retval  = ind1 + "\"nodes\":[" + nl
        retval += ind2 + (ind2 + ",").join(ns)
        retval += ind1 + "]," + nl
        return retval

    def con_edges(self):
        nl = self.con_newline()
        ind1 = self.con_indent(2)
        ind2 = self.con_indent(4)
        ind3 = self.con_indent(6)
        def create_edge(x):
            retval  = "{" + nl
            retval += ind3 + "\"source\":" + str(x["source"]) + ","  + nl
            retval += ind3 + "\"target\":" + str(x["target"]) + "," + nl
            retval += ind3 + "\"label\":\"" + x["label"] + "\"" + nl
            retval += ind2 + "}" + nl
            #print(x["source_name"] + " -[" + x["label"] + "]> " + x["target_name"])
            return retval

        edges = [create_edge(x) for x in self.edges]
        retval  = ind1 + "\"edges\":[" + nl
        retval += ind2 + (ind2 + ",").join(edges)
        retval += ind1 + "]" + nl
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

    def toString(self,framework,flavor=2,include_anchs=True,testing_mode=False):
        self.flavor = flavor
        self.include_anchs = include_anchs
        self.testing_mode = testing_mode
        nl = self.con_newline()
        retval = "{" + nl
        retval += self.con_header(framework)
        retval += self.con_tops()
        retval += self.con_nodes()
        retval += self.con_edges()
        retval += "}" + nl
        return retval

def xml2mrp(fname,id0,do_cutoff=True):
    with open("../ProcessModels/" + fname,"r") as f:
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
    mrp = Mrp(parser,fname,id0,do_cutoff=do_cutoff)
    return mrp









"""
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN
"""

def sort_files(fs,stype_fun):
    no_anchs = ['P05.xml', 'P06.xml', 'P15.xml', 'P16.xml', 'P18.xml', 'P19.xml', 'P20.xml', 'P23.xml', 'P25.xml' 'P30.xml']
    stypes = {"normal":1,"anchs-first":2,"none":3}
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
    elif stype == stypes["anchs-first"]:
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
    fs = sort_files(fs,lambda t: t["anchs-first"])
    res = []
    descs = []
    id0 = 1
    flavor = 1

    testing_mode = False
    if testing_mode:
        m0 = xml2mrp("P34.xml",1)
        r0 = m0.toString("dcr",flavor,True,testing_mode=False)
        a0 = m0.test_anchors()
        print(r0)
        print(a0)
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

