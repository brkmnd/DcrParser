from mrp2dcr.dcr2mrp import xml2mrp,save_data
import os

def main_dcr2mrp():
    fwork = "dcr"
    flavor = 1

    g_annon = None
    g_nonannon = None

    fs_annon = os.listdir("ProcessModels/rev1/annotated")
    fs_notannon = os.listdir("ProcessModels/rev1/not-annotated")
    fs_annon.sort()
    fs_notannon.sort()

    res1 = []
    res2 = []
    descs = []
    id0 = 1

    do_single = True
    if do_single:
        fname = "rev1/annotated/" + fs_annon[3]
        fname = "simplified/P02-simple.xml"

        print("do single for '" + fname + "'")

        mrp = xml2mrp(fname,1)

        res_g = mrp.toString(framework=fwork,flavor=flavor)
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
    
    res_train = [x.toString(framework=fwork,flavor=flavor) for x in res1]
    res_val = [x.toString(fwork,flavor) for x in res2[:-5]]
    res_eval = [x.create_input() for x in res1 + res2[:-5]]


    save_data("\n".join(res_train),"training/dcr.mrp")
    save_data("\n".join(res_val),"validation/dcr.mrp")
    save_data("\n".join(res_eval),"evaluation/input.mrp")
    save_data("\n".join(descs),"companion/udpipe.txt")


if __name__ == "__main__":
    main_dcr2mrp()
