import json

def file2lines(fname):
    res = None
    with open("../mrp_data/2020/cf/training/" + fname,"r") as f:
        res = []
        for l in f:
            res.append(l)
    return res

def xml2file(fname,cont):
    with open(fname,"w") as f:
        f.write(cont)

class XmlPrinter():
    
    str_act = "Activity"

    def __init__(this,title,graph):
        this.title = title
        this.graph = graph
        this.desc = graph["input"]

        this.events = []
        this.roles = []
        this.labelmap = {}
        this.labels = []
        this.highlighter = []

        this.constraints = {
                  "condition":{"name":"conditions","data":[]}
                , "response":{"name":"responses","data":[]}
                , "coresponse":{"name":"coresponses","data":[]}
                , "exclude":{"name":"excludes","data":[]}
                , "include":{"name":"includes","data":[]}
                , "milestone":{"name":"milestones","data":[]}
                }

    def find_activities(this,label):
        res = []
        for act in this.labelmap.keys():
            for l0 in this.labelmap[act]:
                if l0 == label:
                    res.append(act)
        return res

    def con_ident(this,n):
        return "  " * 2 * n
    def con_nl(this,n):
        return "\n" * n
    def con_eventloc(this):
        nr_events = len(this.events)
        x_off,y_off = 250,250
        x,y = x_off + (nr_events % 4) * x_off,y_off + y_off * (nr_events // 4)
        res = "<location xLoc=\"" + str(x) + "\" yLoc=\"" + str(y) + "\"/>"
        return res

    def add_event(this,n):
        nl = this.con_nl(1)
        nr_events = len(this.events)
        def create_eventdesc():
            desc = n["label"]
            return "&lt;p&gt;" + desc + "&lt;/p&gt;"
        res  = this.con_ident(4) + "<event id=\"" + this.str_act + str(n["id"]) + "\">" + nl
        res += this.con_ident(5) + "<precondition message=\"\"/>" + nl
        res += this.con_ident(5) + "<custom>" + nl
        res += this.con_ident(6) + "<visualization>" + nl
        res += this.con_ident(7) + this.con_eventloc() + nl
        res += this.con_ident(7) + "<colors bg=\"#f9f7ed\" textStroke=\"#000000\" stroke=\"#cccccc\"/>" + nl
        res += this.con_ident(6) + "</visualization>" + nl
        res += this.con_ident(6) + "<roles>" + nl
        res += this.con_ident(7) + "<role>" + n["role"] + "</role>" + nl
        res += this.con_ident(6) + "</roles>" + nl
        res += this.con_ident(6) + "<groups>" + nl
        res += this.con_ident(7) + "<group/>" + nl
        res += this.con_ident(6) + "</groups>" + nl
        res += this.con_ident(6) + "<phases>" + nl
        res += this.con_ident(7) + "<phase/>" + nl
        res += this.con_ident(6) + "</phases>" + nl
        res += this.con_ident(6) + "<eventType/>" + nl
        res += this.con_ident(6) + "<eventScope>private</eventScope>" + nl
        res += this.con_ident(6) + "<eventTypeData/>" + nl
        res += this.con_ident(6) + "<eventDescription>" + create_eventdesc() + "</eventDescription>" + nl
        res += this.con_ident(6) + "<purpose/>" + nl
        res += this.con_ident(6) + "<guide/>" + nl
        res += this.con_ident(6) + "<insight use=\"false\"/>" + nl
        res += this.con_ident(6) + "<level>1</level>" + nl
        res += this.con_ident(6) + "<sequence>" + str(nr_events + 1) + "</sequence>" + nl
        res += this.con_ident(6) + "<costs>0</costs>" + nl
        res += this.con_ident(6) + "<eventData/>" + nl
        res += this.con_ident(6) + "<interfaces/>" + nl
        res += this.con_ident(5) + "</custom>" + nl
        res += this.con_ident(4) + "</event>"
        this.events.append(res)
    def add_role(this,n):
        res  = "<role description=\"" + n["label"] + "\" specification=\"\">"
        res += n["label"]
        res += "</role>"
        this.roles.append(res)
    def add_label(this,n):
        if "#role" not in n:
            res  = this.con_ident(4)
            res += "<label id=\"" + n["label"] + "\"/>"
            this.labels.append(res)
    def add_labelmap(this,n):
        #this.labelmaps.append(res)
        aid = this.str_act + str(n["id"])
        alabel = n["label"]
        if "#role" in n:
            return
        if aid not in this.labelmap:
            this.labelmap[aid] = []
        this.labelmap[aid].append(alabel)
    def add_constraint(this,e):
        l = e["label"]
        if l != "role":
            res  = this.con_ident(4)
            res += "<" + l + " "
            res += "sourceId=\"" + this.str_act + str(e["source"]) + "\" "
            res += "targetId=\"" + this.str_act + str(e["target"]) + "\" "
            res += " filterLevel=\"0\" description=\"\" time=\"\" groups=\"\" "
            res += "/>"
            this.constraints[l]["data"].append(res)
    def add_highlightdesc(this,desc):
        nl = this.con_nl(1)
        res  = this.con_ident(5) + "<highlightLayers>" + nl
        res += this.con_ident(6) + "<highlightLayer default=\"true\" name=\"description\">"
        res += desc
        res += "</highlightLayer>" + nl
        res += this.con_ident(5) + "</highlightLayers>"
        this.highlighter.append(res)
    def add_highlights(this,ns):
        nl = this.con_nl(1)
        res  = this.con_ident(5) + "<highlights>" + nl
        for n in ns:
            if "anchors" not in n or len(n["anchors"]) == 0:
                continue
            if "#role" in n:
                r = "role"
            else:
                r = n["role"]
            if r != "role":
                res += this.con_ident(6) + "<highlight type=\"activity\">" + nl
            else:
                res += this.con_ident(6) + "<highlight type=\"" + r + "\">" + nl
            res += this.con_ident(7) + "<layers>" + nl
            res += this.con_ident(8) + "<layer name=\"description\">" + nl
            res += this.con_ident(9) + "<ranges>" + nl
            for a in n["anchors"]:
                res += this.con_ident(10)
                res += "<range start=\"" + str(a["from"]) + "\" end=\"" + str(a["to"]) + "\">" 
                res += n["label"]
                res += "</range>"
                res += nl
            res += this.con_ident(9) + "</ranges>" + nl
            res += this.con_ident(8) + "</layer>" + nl
            res += this.con_ident(7) + "</layers>" + nl
            res += this.con_ident(7) + "<items>" + nl
            for act in this.find_activities(n["label"]):
                res += this.con_ident(8) + "<item id=\"" + act + "\"/>" + nl
            res += this.con_ident(7) + "</items>" + nl
            res += this.con_ident(6) + "</highlight>" + nl
        res += this.con_ident(5) + "</highlights>" + nl
        this.highlighter.append(res)

    def print_events(this):
        nl = this.con_nl(1)
        res  = this.con_ident(3) + "<events>" + nl
        res += "\n".join(this.events) + nl
        res += this.con_ident(3) + "</events>" + nl
        res += this.con_ident(3) + "<subProcesses/>" + nl
        res += this.con_ident(3) + "<distribution/>" + nl
        return res
    def print_roles(this):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<roles>" + nl
        for r in this.roles:
            res += this.con_ident(5) + r + nl
        res += this.con_ident(4) + "</roles>" + nl
        return res
    def print_gdetails(this):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<groups/>" + nl
        res += this.con_ident(4) + "<phases/>" + nl
        res += this.con_ident(4) + "<eventTypes/>" + nl
        res += this.con_ident(4) + "<eventParameters/>" + nl
        res += this.con_ident(4) + "<graphDetails>" + this.desc + "</graphDetails>" + nl
        res += this.con_ident(4) + "<graphLanguage>en-US</graphLanguage>" + nl
        res += this.con_ident(4) + "<graphDomain>process</graphDomain>" + nl
        res += this.con_ident(4) + "<graphFilters>" + nl
        res += this.con_ident(5) + "<filteredGroups/>" + nl
        res += this.con_ident(5) + "<filteredRoles/>" + nl
        res += this.con_ident(5) + "<filteredPhases/>" + nl
        res += this.con_ident(4) + "</graphFilters>" + nl
        return res
    def print_labels(this):
        nl = this.con_nl(1)
        res  = this.con_ident(3) + "<labels>" + nl
        res += "\n".join(this.labels) + nl
        res += this.con_ident(3) + "</labels>" + nl
        return res
    def print_labelmaps(this):
        nl = this.con_nl(1)
        res  = this.con_ident(3) + "<labelMappings>" + nl
        for aid in this.labelmap.keys():
            for ltarget in this.labelmap[aid]:
                res += this.con_ident(4)
                res += "<labelMapping "
                res += "eventId=\"" + aid + "\" "
                res += "labelId=\"" + ltarget + "\""
                res += "/>" + nl
        res += this.con_ident(3) + "</labelMappings>" + nl
        res += this.con_ident(3) + "<expressions/>" + nl
        res += this.con_ident(3) + "<variables/>" + nl
        res += this.con_ident(3) + "<variableAccesses>" + nl
        res += this.con_ident(4) + "<writeAccesses/>" + nl
        res += this.con_ident(3) + "</variableAccesses>" + nl
        return res
    def print_keywords(this):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<keywords>BPMAI, Demo, Highlighter tool</keywords>" + nl
        return res
    def print_highlighter(this):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<hightlighterMarkup id=\"HLM\"/>" + nl
        res += this.con_ident(4) + "<highlighterMarkup>" + nl
        res += "\n".join(this.highlighter)
        res += this.con_ident(4) + "</highlighterMarkup>" + nl
        return res
    def print_constraints(this):
        nl = this.con_nl(1)
        res  = this.con_ident(2) + "<constraints>" + nl
        for ck in this.constraints.keys():
            c = this.constraints[ck]
            res += this.con_ident(3) + "<" + c["name"] + ">" + nl
            res += "\n".join(c["data"]) + nl
            res += this.con_ident(3) + "</" + c["name"] + ">" + nl
        res += this.con_ident(3) + "<spawns />" + nl # is this used for something
        res += this.con_ident(2) + "</constraints>" + nl
        return res
    def print_restag(this,inner):
        nl = this.con_nl(1)
        res  = this.con_ident(2) + "<resources>" + nl
        res += inner
        res += this.con_ident(2) + "</resources>" + nl
        return res
    def print_customtag(this,inner):
        nl = this.con_nl(1)
        res  = this.con_ident(3) + "<custom>" + nl
        res += inner
        res += this.con_ident(3) + "</custom>" + nl
        return res
    def print_spectag(this,inner):
        nl = this.con_nl(1)
        res  = this.con_ident(1) + "<specification>" + nl
        res += inner
        res += this.con_ident(1) + "</specification>" + nl
        return res
    def print_runtime(this):
        nl = this.con_nl(1)
        res  = this.con_ident(1) + "<runtime>" + nl
        res += this.con_ident(2) + "<custom>" + nl
        res += this.con_ident(3) + "<globalMarking/>" + nl
        res += this.con_ident(2) + "</custom>" + nl
        res += this.con_ident(2) + "<marking>" + nl
        res += this.con_ident(3) + "<globalStore/>" + nl
        res += this.con_ident(3) + "<executed/>" + nl
        res += this.con_ident(3) + "<included>" + nl

        for act in this.labelmap.keys():
            res += this.con_ident(4) + "<event id=\"" + act + "\"/>" + nl

        res += this.con_ident(3) + "</included>" + nl
        res += this.con_ident(3) + "<pendingResponses />" + nl
        res += this.con_ident(2) + "</marking>" + nl
        res += this.con_ident(1) + "</runtime>" + nl
        return res
    def print_outertag(this,inner):
        nl   = this.con_nl(1)
        res  = "<dcrgraph title=\"" + this.title + "\" "
        res += "dataTypesStatus=\"hide\" filterLevel=\"-1\" insightFilter=\"false\" "
        res += "zoomLevel=\"-1\" formGroupStyle=\"Normal\" formLayoutStyle=\"Horizontal\" "
        res += "graphBG=\"#EBEBEB\" graphType=\"0\">" + nl
        res += inner
        res += "</dcrgraph>"
        return res

    def toString(this):
        res  = this.print_events()
        res += this.print_labels()
        res += this.print_labelmaps()
        res += this.print_customtag(
                  this.print_keywords()
                + this.print_roles()
                + this.print_gdetails()
                + this.print_highlighter()
                )
        res  = this.print_restag(res)
        res += this.print_constraints()
        res  = this.print_spectag(res)
        res += this.print_runtime()
        res  = this.print_outertag(res)
        return res
        

class MrpParser():
    def __init__(this,graph):
        res = ""
        this.graph = graph
        this.edges = graph["edges"]
        this.nodes = graph["nodes"]
        this.tops = graph["tops"]
        this.desc = graph["input"]

        this.xml_printer = XmlPrinter(graph["source"].replace(".xml",""),graph)

        this.add_roles()

    def find_role(this,n):
        rid = -1
        nid = n["id"]
        for e in this.edges:
            if e["label"] == "role" and e["source"] == nid:
                rid = e["target"]
        res = None
        if rid > -1:
            for n in this.nodes:
                if n["id"] == rid:
                    res = n["label"]
        if res is None:
            print("no role for " + str(n))
            res = ""
        return res

    def add_roles(this):
        for n in this.nodes:
            if n["id"] in this.tops:
                n["role"] = this.find_role(n)
            else:
                n["#role"] = True

    def create_events(this):
        for n in this.nodes:
            if n["id"] in this.tops:
                this.xml_printer.add_event(n)
            else:
                this.xml_printer.add_role(n)

    def create_labelmaps(this):
        for n in this.nodes:
            this.xml_printer.add_label(n)
            this.xml_printer.add_labelmap(n)

    def create_constraints(this):
        for e in this.edges:
            this.xml_printer.add_constraint(e)

    def create_highlighter(this):
        this.xml_printer.add_highlightdesc(this.desc)
        this.xml_printer.add_highlights(this.nodes)
        

    def toString(this):
        this.create_events()
        this.create_labelmaps()
        this.create_constraints()
        this.create_highlighter()
        #res = this.xml_printer.print_events()
        #res = this.xml_printer.print_highlighter()
        res = this.xml_printer.toString()
        
        return res

"""
MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN
MAIN MAIN MAIN MAIN
"""

def main():
    ts = file2lines("dcr.mrp")
    jts = [json.loads(t) for t in ts]
    parser = MrpParser(jts[0])
    res = parser.toString()
    xml2file("P02simple-back.xml",res)

if __name__ == "__main__":
    main()
