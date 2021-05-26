from dcr2mrp import xml2mrp
import numpy as np
import os

def save_data(txt,fname):
    fname = "../mrp_data/2020/cf/" + fname
    with open(fname,"w") as f:
        f.write(txt)
    print("saved '" + fname + "'")

def main_dcr2mrp():
    fwork = "dcr"
    flavor = 1

    g_annon = None
    g_nonannon = None

    fs_annon = os.listdir("../ProcessModels/rev1/annotated")
    fs_notannon = os.listdir("../ProcessModels/rev1/not-annotated")
    fs_notrev = os.listdir("../ProcessModels")
    fs_annon.sort()
    fs_notannon.sort()

    res1 = []
    res2 = []
    res_notrev = []
    descs = []
    id0 = 1
    id1 = 1

    do_single = True
    if do_single:
        fname = "simplified/P02-simple.xml"

        print("do single for '" + fname + "'")

        mrp = xml2mrp(fname,1)

        res_g = mrp.toString(framework=fwork,flavor=flavor,testing_mode=True)
        res_eval = mrp.create_input()
        res_d = mrp.desc

        save_data(res_g,"training/dcr.mrp")
        save_data(res_g,"validation/dcr.mrp")
        save_data(res_eval,"evaluation/input.mrp")
        save_data(res_d,"companion/udpipe.txt")
        return True

    for f in fs_annon:
        fname = "rev1/annotated/" + f
        mrp = xml2mrp(fname,id0)
        res1.append(mrp)
        descs.append(mrp.desc)
        id0 += 1
    for f in fs_notannon:
        fname = "rev1/not-annotated/" + f
        mrp = xml2mrp(fname,id0,do_cutoff=True)
        res2.append(mrp)
        descs.append(mrp.desc)
        id0 += 1
    for fname in fs_notrev:
        if fname[-4:] != ".xml":
            continue
        mrp = xml2mrp(fname,id1)
        res_notrev.append(mrp)
        id1 += 1

    do_stats = True
    if do_stats:
        res_stats = res1 + res2
        res_stats = res_notrev
        full_desc_counts = np.array([r.stats["full desc count"] for r in res_stats])
        desc_counts = np.array([r.stats["desc count"] for r in res_stats])
        node_counts = np.array([r.stats["nr nodes"] for r in res_stats])
        print("desc count: " + str(desc_counts.mean()))
        print("full desc count: "  + str(full_desc_counts.mean()))
        print("node count: " + str(node_counts.mean()))
        return True
    
    res_train = [x.toString(framework=fwork,flavor=flavor) for x in res1]
    res_val = [x.toString(fwork,flavor) for x in res2[:-5]]
    res_test = [x.create_input() for x in res2[5:]]


    save_data("\n".join(res_train),"training/dcr.mrp")
    save_data("\n".join(res_val),"validation/dcr.mrp")
    save_data("\n".join(res_test),"evaluation/input.mrp")
    save_data("\n".join(descs),"companion/udpipe.txt")


if __name__ == "__main__":
    main_dcr2mrp()
