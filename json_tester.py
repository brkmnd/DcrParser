import json


def load_txt(fname):
    res = ""
    with open(fname,"r") as f:
        res = f.read()
    return res

t1 = load_txt("models/2020/cf/training/ucca.mrp")


data = json.loads(t1)
res = json.dump(data)
print(res)

