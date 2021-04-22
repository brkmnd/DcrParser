import json

def file2lines(fname):
    res = None
    with open("../mrp_data/2020/cf/training/" + fname,"r") as f:
        res = []
        for l in f:
            res.append(l)
    return res

class XmlPrinter():
    
    str_act = "Activity"

    def __init__(this,title):
        this.title = title

        this.events = []
        this.roles = []
        this.labelmaps = []
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

    def con_ident(this,n):
        return "  " * n
    def con_nl(this,n):
        return "\n" * n

    def add_event(this,n):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<event id=\"" + this.str_act + str(n["id"]) + "\">" + nl
        res += this.con_ident(6) + "<roles>" + nl
        res += this.con_ident(7) + "<role>" + n["role"] + "</role>" + nl
        res += this.con_ident(6) + "</roles>" + nl
        res += this.con_ident(6) + "<eventDescription>" + n["label"] + "</eventDescription>" + nl
        res += this.con_ident(4) + "</event>"
        this.events.append(res)
    def add_role(this,n):
        res  = "<role description=\"" + n["label"] + "\" specification="">"
        res += n["label"]
        res += "</role>"
        this.roles.append(res)
    def add_label(this,n):
        res  = this.con_ident(4)
        res += "<label id=\"" + n["label"] + "\"/>"
        this.labels.append(res)
    def add_labelmap(this,n):
        res  = this.con_ident(4)
        res += "<labelMapping "
        res += "eventId=\"" + this.str_act + str(n["id"]) + "\" "
        res += "labelId=\"" + n["label"] + "\""
        res += "/>"
        this.labelmaps.append(res)
    def add_constraint(this,e):
        l = e["label"]
        if l != "role":
            res  = this.con_ident(4)
            res += "<" + l + " "
            res += "sourceId=\"" + this.str_act + str(e["source"]) + "\" "
            res += "targetId=\"" + this.str_act + str(e["target"]) + "\" "
            res += "/>"
            this.constraints[l]["data"].append(res)
    def add_highlightdesc(this,desc):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<highlightLayers>" + nl
        res += this.con_ident(5) + "<highlightLayer default=\"true\" name=\"description\">" + nl
        res += desc
        res += this.con_ident(5) + "</highlightLayer>" + nl
        res += this.con_ident(4) + "</highlightLayers>" + nl
        this.highlighter.append(res)
    def add_highlights(this,ns):
        nl = this.con_nl(1)
        res  = this.con_ident(4) + "<highlights>" + nl
        for n in ns:
            if "anchors" not in n or len(n["anchors"]) == 0:
                continue
            if "#role" in n:
                r = "role"
            else:
                r = n["role"]
            res += this.con_ident(5) + "<highlight type=\"" + r + "\">" + nl
            res += this.con_ident(6) + "<layers>" + nl
            res += this.con_ident(7) + "<layer name=\"description\">" + nl
            res += this.con_ident(8) + "<ranges>" + nl
            for a in n["anchors"]:
                res += this.con_ident(9)
                res += "<range start=\"" + str(a["from"]) + "\" end=\"" + str(a["to"]) + "\">" 
                res += n["label"]
                res += "</range>"
                res += nl
            res += this.con_ident(8) + "</ranges>" + nl
            res += this.con_ident(7) + "</layer>" + nl
            res += this.con_ident(6) + "</layers>" + nl
            res += this.con_ident(5) + "</highlight>" + nl
        res += this.con_ident(4) + "</highlights>" + nl
        this.highlighter.append(res)

    def print_events(this):
        nl = this.con_nl(1)
        res  = this.con_ident(3) + "<events>" + nl
        res += "\n".join(this.events) + nl
        res += this.con_ident(3) + "</events>" + nl
        return res
    def print_roles(this):
        nl = this.con_nl(1)
        res  = this.con_ident(3) + "<roles>" + nl
        for r in this.roles:
            res += this.con_ident(4) + r + nl
        res += this.con_ident(3) + "</roles>" + nl
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
        res += "\n".join(this.labelmaps) + nl
        res += this.con_ident(3) + "</labelMappings>" + nl
        return res
    def print_highlighter(this):
        nl = this.con_nl(1)
        res  = this.con_ident(2) + "<hightlighterMarkup id=\"HLM\"/>" + nl
        res += this.con_ident(2) + "<highlighterMarkup>" + nl
        res += this.con_ident(2) + "</highlighterMarkup>" + nl
        res += "\n".join(this.highlighter)
        return res
    def print_constraints(this):
        nl = this.con_nl(1)
        res  = this.con_ident(2) + "<constraints>" + nl
        for ck in this.constraints.keys():
            c = this.constraints[ck]
            res += this.con_ident(3) + "<" + c["name"] + ">" + nl
            res += "\n".join(c["data"]) + nl
            res += this.con_ident(3) + "</" + c["name"] + ">" + nl
        res += this.con_ident(2) + "<constraints>" + nl
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
        res  = this.con_ident(1) + "</specification>" + nl
        res += inner
        res += this.con_ident(1) + "<specification>" + nl
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
                  this.print_roles()
                + this.print_highlighter()
                )
        res += this.print_constraints()
        res  = this.print_spectag(res)
        res  = this.print_outertag(res)
        print(res)
        return res
        

class MrpParser():

    def __init__(this,graph):
        res = ""
        this.graph = graph
        this.edges = graph["edges"]
        this.nodes = graph["nodes"]
        this.tops = graph["tops"]
        this.desc = graph["input"]

        this.xml_printer = XmlPrinter(graph["source"].replace(".xml",""))

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

        #print(res)

def main():
    ts = file2lines("dcr.mrp")
    jts = [json.loads(t) for t in ts]
    parser = MrpParser(jts[0])
    parser.toString()


if __name__ == "__main__":
    main()
