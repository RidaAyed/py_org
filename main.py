import py_org


def parse_json(path):
    f = open(path, "r")
    contents = f.read()
    q.add_parse(contents)
    f.close()


def write_output(path, contents):
    f = open(path, "a")
    f.write(contents)
    f.close()


q = py_org.Org()
parse_json("input1.json")
parse_json("input2.json")
write_output("journal.org", str(q))
